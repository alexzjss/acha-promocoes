"""
Conversor da fila de afiliados.

- Lojas com regra por URL (Amazon, redes): convertidas na hora.
- Mercado Livre: usa o gerador de links do portal de Afiliados com uma
  sessão logada guardada em data/perfil_ml_afiliados (faça o login uma
  vez com `python scripts/login_afiliados_ml.py`).
"""

import re
from pathlib import Path

from playwright.async_api import async_playwright

from services.afiliados import chave_loja, converter_por_regra, tem_regra
from services.afiliados_db import (
    buscar_pendentes,
    inicializar_banco,
    marcar_convertido,
    registrar_erro,
)


BASE_DIR = Path(__file__).resolve().parent.parent
PERFIL_ML = BASE_DIR / "data" / "perfil_ml_afiliados"

URL_GERADOR_ML = "https://www.mercadolivre.com.br/afiliados/linkbuilder"

PADRAO_LINK_ML = re.compile(
    r"https?://(?:meli\.la|mercadolivre\.com/sec)/[\w\-]+"
)

MAX_TENTATIVAS = 5


class SessaoML(Exception):
    """Sessão do portal de Afiliados não está logada."""


async def _textos_da_pagina(page):
    """Texto visível + valores de campos (o link pode estar num input)."""

    corpo = await page.inner_text("body")

    valores = await page.eval_on_selector_all(
        "input, textarea", "els => els.map(e => e.value || '')"
    )

    return corpo + "\n" + "\n".join(valores)


async def gerar_link_ml(page, url_original):
    await page.goto(URL_GERADOR_ML, wait_until="domcontentloaded")
    await page.wait_for_timeout(2500)

    if "login" in page.url or "registration" in page.url:
        raise SessaoML("sessão do portal de Afiliados expirada")

    antes = set(PADRAO_LINK_ML.findall(await _textos_da_pagina(page)))

    campo = page.locator(
        "textarea:visible, input[type='text']:visible, "
        "input[type='url']:visible"
    ).first
    await campo.fill(url_original)

    botao = page.get_by_role("button", name=re.compile("gerar", re.I)).first
    await botao.click()

    for _ in range(20):
        await page.wait_for_timeout(500)

        novos = [
            link
            for link in PADRAO_LINK_ML.findall(await _textos_da_pagina(page))
            if link not in antes
        ]

        if novos:
            return novos[0]

    raise RuntimeError("o gerador não devolveu um link")


async def converter_pendentes(limite=15):
    """Processa a fila; retorna {'convertidos': n, 'erros': n}."""

    inicializar_banco()

    pendentes = [
        p
        for p in buscar_pendentes(limite=limite * 4)
        if p["tentativas"] < MAX_TENTATIVAS
    ][:limite]

    resumo = {"convertidos": 0, "erros": 0}

    if not pendentes:
        return resumo

    ml = []

    for item in pendentes:
        if tem_regra(item["loja"]):
            link = converter_por_regra(item["loja"], item["url_original"])

            if link:
                marcar_convertido(item["loja"], item["item_id"], link)
                resumo["convertidos"] += 1

        elif chave_loja(item["loja"]) == "MERCADOLIVRE":
            ml.append(item)

    if not ml:
        return resumo

    if not PERFIL_ML.exists():
        print(
            "ℹ️ Afiliados ML: faça login uma vez com "
            "`python scripts/login_afiliados_ml.py`."
        )
        return resumo

    async with async_playwright() as p:
        contexto = await p.chromium.launch_persistent_context(
            str(PERFIL_ML), headless=True, locale="pt-BR"
        )

        try:
            page = (
                contexto.pages[0]
                if contexto.pages
                else await contexto.new_page()
            )

            for item in ml:
                try:
                    link = await gerar_link_ml(page, item["url_original"])

                except SessaoML as erro:
                    print(
                        f"🔒 Afiliados ML: {erro}. "
                        "Rode scripts/login_afiliados_ml.py."
                    )
                    break

                except Exception as erro:
                    registrar_erro(item["loja"], item["item_id"], erro)
                    resumo["erros"] += 1
                    print(f"⚠️ Afiliado {item['item_id']}: {erro}")
                    continue

                marcar_convertido(item["loja"], item["item_id"], link)
                resumo["convertidos"] += 1
                print(f"🔗 Link afiliado ML gerado: {link}")

        finally:
            await contexto.close()

    return resumo


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(converter_pendentes()))
