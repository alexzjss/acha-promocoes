"""
Utilidades compartilhadas pelos coletores de lojas.
"""

import re
from urllib.parse import urljoin


PRECO_MINIMO = 10.00
DESCONTO_MINIMO = 5.00
DESCONTO_MAXIMO = 70.00

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0 Safari/537.36"
)

_REGEX_PRECO = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")

_TERMOS_PARCELAMENTO = (
    "x de r$",
    "x r$",
    "vezes de r$",
    "parcela",
    "sem juros",
    "em até",
    "em ate",
)


def converter_preco(texto):
    """
    "R$ 1.299,90" -> 1299.90. Retorna None se não houver preço.
    """

    if not texto:
        return None

    resultado = _REGEX_PRECO.search(str(texto))

    if not resultado:
        return None

    valor = resultado.group(1).replace(".", "").replace(",", ".")

    try:
        return float(valor)

    except ValueError:
        return None


def linha_eh_parcelamento(linha):
    linha = linha.lower()

    return any(termo in linha for termo in _TERMOS_PARCELAMENTO)


def extrair_precos(texto):
    """
    Extrai os preços (sem repetidos, na ordem) de um texto de card,
    ignorando linhas de parcelamento. Aceita tanto "R$ 199,99"
    na mesma linha quanto "R$" e "199,99" em linhas separadas.
    """

    if not texto:
        return []

    linhas = [l.strip() for l in texto.splitlines() if l.strip()]

    precos = []
    indice = 0

    while indice < len(linhas):
        linha = linhas[indice]

        if linha_eh_parcelamento(linha):
            indice += 1
            continue

        if linha == "R$" and indice + 1 < len(linhas):
            proxima = linhas[indice + 1]

            if not linha_eh_parcelamento(proxima):
                preco = converter_preco(proxima)

                if preco is not None:
                    precos.append(preco)

            indice += 2
            continue

        if "R$" in linha:
            for trecho in re.split(r"R\$", linha)[1:]:
                preco = converter_preco(trecho)

                if preco is not None:
                    precos.append(preco)

        indice += 1

    unicos = []

    for preco in precos:
        if preco not in unicos:
            unicos.append(preco)

    return unicos


def calcular_desconto(preco_anterior, preco_atual):
    if not preco_anterior or preco_anterior <= 0 or preco_atual is None:
        return 0.0

    return (preco_anterior - preco_atual) / preco_anterior * 100


def validar_precos(nome, preco_anterior, preco_atual):
    """
    Barreira básica antes de enviar ao pipeline: preços coerentes
    e desconto dentro de uma faixa plausível.
    """

    if preco_anterior is None or preco_atual is None:
        return False

    if preco_anterior < PRECO_MINIMO or preco_atual < PRECO_MINIMO:
        return False

    if preco_atual >= preco_anterior:
        return False

    desconto = calcular_desconto(preco_anterior, preco_atual)

    if desconto < DESCONTO_MINIMO:
        return False

    if desconto > DESCONTO_MAXIMO:
        print(
            f"🚨 Desconto suspeito descartado: {nome} "
            f"(R$ {preco_anterior:.2f} -> R$ {preco_atual:.2f}, "
            f"{desconto:.2f}% OFF)"
        )
        return False

    return True


def normalizar_url(base_url, url, remover_query=True):
    if not url:
        return None

    url = urljoin(base_url, url).split("#")[0]

    if remover_query:
        url = url.split("?")[0]

    return url


def escolher_nome(texto, minimo=12):
    """
    Heurística: a linha mais longa que não seja preço, desconto
    ou parcelamento costuma ser o nome do produto.
    """

    candidatos = []

    for linha in texto.splitlines():
        linha = linha.strip()

        if len(linha) < minimo:
            continue

        if "R$" in linha or linha_eh_parcelamento(linha):
            continue

        if re.fullmatch(r"[-\d.,%\s]+", linha):
            continue

        candidatos.append(linha)

    if not candidatos:
        return None

    return max(candidatos, key=len)


async def coletar_cards_playwright(
    *,
    loja,
    url_pagina,
    base_url,
    seletor_card,
    seletor_link,
    limite=20,
    espera_ms=4000,
    remover_query=True,
    seletor_nome=None,
):
    """
    Coletor genérico baseado em Playwright para lojas cujo HTML
    precisa ser renderizado. Para cada card, assume que os dois
    primeiros preços "limpos" são [preço anterior, preço atual] e
    usa o maior/menor como proteção contra ordem invertida.

    Retorna produtos no formato do deal_processor.
    """

    from playwright.async_api import async_playwright

    print("\n" + "=" * 60)
    print(f"🛒 COLETOR {loja.upper()}")
    print("=" * 60)

    produtos = []
    urls_vistas = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        try:
            context = await browser.new_context(
                locale="pt-BR",
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080},
            )

            page = await context.new_page()

            try:
                resposta = await page.goto(
                    url_pagina,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                if resposta:
                    print(f"🌐 {loja} respondeu: {resposta.status}")

                await page.wait_for_timeout(espera_ms)

                # Dispara carregamento preguiçoso de imagens/cards.
                for _ in range(4):
                    await page.mouse.wheel(0, 3000)
                    await page.wait_for_timeout(1000)

            except Exception as erro:
                print(f"❌ Erro acessando {loja}: {erro}")
                return []

            cards = page.locator(seletor_card)
            total = await cards.count()

            print(f"🔎 Cards encontrados: {total}")

            for indice in range(total):
                if len(produtos) >= limite:
                    break

                try:
                    card = cards.nth(indice)
                    # seletor_link=None -> o próprio card é o link.
                    link = (
                        card.locator(seletor_link).first
                        if seletor_link
                        else card
                    )

                    if await link.count() == 0:
                        continue

                    url = normalizar_url(
                        base_url,
                        await link.get_attribute("href"),
                        remover_query,
                    )

                    if not url or url in urls_vistas:
                        continue

                    texto = (await card.inner_text()).strip()

                    if not texto:
                        continue

                    nome = None

                    if seletor_nome:
                        el = card.locator(seletor_nome).first

                        if await el.count() > 0:
                            nome = (await el.inner_text()).strip()

                    nome = nome or (
                        await link.get_attribute("title")
                        or await link.get_attribute("aria-label")
                        or escolher_nome(texto)
                        or (await link.inner_text()).strip().splitlines()[0]
                    )

                    if not nome or len(nome.strip()) < 8:
                        continue

                    precos = extrair_precos(texto)

                    if len(precos) < 2:
                        continue

                    preco_anterior = max(precos[:2])
                    preco_atual = min(precos[:2])

                    if not validar_precos(nome, preco_anterior, preco_atual):
                        continue

                    imagem = None
                    img = card.locator("img").first

                    if await img.count() > 0:
                        imagem = (
                            await img.get_attribute("src")
                            or await img.get_attribute("data-src")
                        )

                        if imagem and imagem.startswith("data:"):
                            imagem = await img.get_attribute("data-src")

                        imagem = normalizar_url(
                            base_url, imagem, remover_query=False
                        )

                    produtos.append(
                        {
                            "nome": nome.strip(),
                            "loja": loja,
                            "preco_anterior": round(preco_anterior, 2),
                            "preco_atual": round(preco_atual, 2),
                            "url": url,
                            "imagem": imagem,
                        }
                    )
                    urls_vistas.add(url)

                    desconto = calcular_desconto(preco_anterior, preco_atual)
                    print(
                        f"✅ {nome.strip()[:70]}\n"
                        f"   R$ {preco_anterior:.2f} -> R$ {preco_atual:.2f} "
                        f"({desconto:.2f}% OFF)"
                    )

                except Exception as erro:
                    print(f"⚠️ Card {indice} ignorado: {erro}")

        finally:
            await browser.close()

    print(f"📦 {loja}: {len(produtos)} ofertas válidas.")

    return produtos
