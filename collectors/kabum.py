import re
from urllib.parse import urljoin

from playwright.async_api import async_playwright


URL_KABUM = "https://www.kabum.com.br/ofertas"
BASE_URL = "https://www.kabum.com.br"

PRECO_MINIMO = 10.00
DESCONTO_MINIMO = 5.00
DESCONTO_MAXIMO = 70.00


def converter_numero_preco(texto):
    """
    Converte:
    1.299,90 -> 1299.90
    299,99   -> 299.99
    """

    if not texto:
        return None

    texto = texto.strip()

    resultado = re.search(
        r"([\d.]+,\d{2})",
        texto
    )

    if not resultado:
        return None

    valor = resultado.group(1)
    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return float(valor)

    except ValueError:
        return None


def normalizar_url(url):
    if not url:
        return None

    url = urljoin(
        BASE_URL,
        url
    )

    url = url.split("#")[0]
    url = url.split("?")[0]

    return url


def linha_eh_parcelamento(linha):
    linha = linha.lower()

    termos = [
        "x de r$",
        "vezes de r$",
        "parcela",
        "parcelas",
        "sem juros",
        "no pix ou",
        "em até",
        "em ate"
    ]

    return any(
        termo in linha
        for termo in termos
    )


def linha_eh_ruido(linha):
    linha_normalizada = linha.lower().strip()

    termos_exatos = [
        "cupom",
        "esquenta",
        "avaliação",
        "avaliacao",
        "desconto:",
        "frete grátis",
        "frete gratis",
        "ver todos",
        "acabaram de chegar"
    ]

    if linha_normalizada in termos_exatos:
        return True

    if linha_normalizada.startswith(
        "avaliação"
    ):
        return True

    if linha_normalizada.startswith(
        "avaliacao"
    ):
        return True

    if linha_normalizada.startswith(
        "desconto"
    ):
        return True

    if re.fullmatch(
        r"-?\d+(?:[.,]\d+)?%",
        linha_normalizada
    ):
        return True

    if re.fullmatch(
        r"\d+(?:[.,]\d+)?",
        linha_normalizada
    ):
        return True

    if linha_eh_parcelamento(
        linha_normalizada
    ):
        return True

    if "r$" in linha_normalizada:
        return True

    return False


def extrair_precos_isolados(texto):
    """
    Interpreta estruturas como:

    R$
    352,93
    R$
    199,99
    Desconto:
    -33%
    No PIX ou 9x de R$ 26,14

    O valor de parcela é ignorado.
    """

    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    precos = []
    indice = 0

    while indice < len(linhas):
        linha = linhas[indice]

        if linha_eh_parcelamento(linha):
            indice += 1
            continue

        # Formato: "R$ 199,99"
        if (
            linha.startswith("R$")
            and len(linha) > 2
        ):
            preco = converter_numero_preco(
                linha
            )

            if preco is not None:
                precos.append(preco)

            indice += 1
            continue

        # Formato:
        # R$
        # 199,99
        if (
            linha == "R$"
            and indice + 1 < len(linhas)
        ):
            proxima_linha = linhas[
                indice + 1
            ]

            if not linha_eh_parcelamento(
                proxima_linha
            ):
                preco = converter_numero_preco(
                    proxima_linha
                )

                if preco is not None:
                    precos.append(preco)

            indice += 2
            continue

        indice += 1

    # Remove valores duplicados mantendo a ordem
    precos_unicos = []

    for preco in precos:
        if preco not in precos_unicos:
            precos_unicos.append(preco)

    return precos_unicos


def extrair_desconto_exibido(texto):
    resultado = re.search(
        r"Desconto:\s*-?\s*(\d+(?:[.,]\d+)?)%",
        texto,
        re.IGNORECASE
    )

    if not resultado:
        return None

    valor = resultado.group(1)
    valor = valor.replace(",", ".")

    try:
        return float(valor)

    except ValueError:
        return None


def extrair_nome_por_texto(texto):
    linhas = [
        linha.strip()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    candidatos = []

    for linha in linhas:
        if linha_eh_ruido(linha):
            continue

        if len(linha) < 12:
            continue

        if linha.lower().startswith(
            "no pix"
        ):
            continue

        candidatos.append(linha)

    if not candidatos:
        return None

    # O nome costuma ser a linha significativa mais longa
    return max(
        candidatos,
        key=len
    )


def validar_precos(
    nome,
    preco_anterior,
    preco_atual,
    desconto_exibido=None
):
    if (
        preco_anterior is None
        or preco_atual is None
    ):
        return False

    if (
        preco_anterior < PRECO_MINIMO
        or preco_atual < PRECO_MINIMO
    ):
        return False

    if preco_atual >= preco_anterior:
        return False

    desconto_calculado = (
        (
            preco_anterior
            - preco_atual
        )
        / preco_anterior
    ) * 100

    if desconto_calculado < DESCONTO_MINIMO:
        return False

    if desconto_calculado > DESCONTO_MAXIMO:
        print(
            f"🚨 Desconto suspeito descartado: "
            f"{nome}"
        )

        print(
            f"   R$ {preco_anterior:.2f}"
            f" -> R$ {preco_atual:.2f}"
            f" ({desconto_calculado:.2f}% OFF)"
        )

        return False

    # O desconto exibido pode considerar cupom ou condição
    # específica. Aceitamos diferença moderada, mas bloqueamos
    # inconsistências muito grandes.
    if desconto_exibido is not None:
        diferenca = abs(
            desconto_calculado
            - desconto_exibido
        )

        if diferenca > 20:
            print(
                f"⚠️ Desconto inconsistente: {nome}"
            )

            print(
                f"   Exibido: "
                f"{desconto_exibido:.2f}%"
            )

            print(
                f"   Calculado: "
                f"{desconto_calculado:.2f}%"
            )

            return False

    return True


async def buscar_ofertas_kabum_vitrine(limite=20):
    print("\n" + "=" * 60)
    print("🟠 COLETOR KABUM")
    print("=" * 60)

    produtos = []
    urls_processadas = set()

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True
        )

        context = await browser.new_context(
            locale="pt-BR",
            viewport={
                "width": 1920,
                "height": 1080
            }
        )

        page = await context.new_page()

        try:
            resposta = await page.goto(
                URL_KABUM,
                wait_until="domcontentloaded",
                timeout=60000
            )

            if resposta:
                print(
                    f"🌐 KaBuM! respondeu: "
                    f"{resposta.status}"
                )

            # Espera os carrosséis renderizarem (tempo fixo era flaky).
            try:
                await page.wait_for_selector(
                    'div.swiper-slide a[href*="/produto/"]',
                    timeout=20000
                )

            except Exception:
                print(
                    "⚠️ KaBuM!: carrosséis não apareceram em 20s."
                )

            await page.wait_for_timeout(
                2000
            )

        except Exception as erro:
            print(
                f"❌ Erro acessando KaBuM!: "
                f"{erro}"
            )

            await browser.close()

            return []

        # Cada carrossel usa swiper-slide.
        # Nem todo swiper-slide é necessariamente produto,
        # então confirmamos a presença do link /produto/.
        cards = page.locator(
            "div.swiper-slide"
        )

        quantidade_cards = await cards.count()

        print(
            f"🔎 Cards encontrados: "
            f"{quantidade_cards}"
        )

        for indice in range(
            quantidade_cards
        ):
            if len(produtos) >= limite:
                break

            card = cards.nth(indice)

            try:
                link = card.locator(
                    'a[href*="/produto/"]'
                ).first

                if await link.count() == 0:
                    continue

                href = await link.get_attribute(
                    "href"
                )

                url = normalizar_url(href)

                if not url:
                    continue

                if url in urls_processadas:
                    continue

                texto = (
                    await card.inner_text()
                ).strip()

                if not texto:
                    continue

                # ==========================================
                # NOME
                # ==========================================

                nome = await link.get_attribute(
                    "title"
                )

                if not nome:
                    nome = await link.get_attribute(
                        "aria-label"
                    )

                if not nome:
                    nome = extrair_nome_por_texto(
                        texto
                    )

                if not nome:
                    continue

                nome = nome.strip()

                # Evita códigos de cupom como nome
                if len(nome) < 12:
                    continue

                # ==========================================
                # PREÇOS
                # ==========================================

                precos = extrair_precos_isolados(
                    texto
                )

                if len(precos) < 2:
                    continue

                # No texto observado:
                # primeiro isolado = preço anterior
                # segundo isolado = preço promocional
                preco_anterior = precos[0]
                preco_atual = precos[1]

                desconto_exibido = (
                    extrair_desconto_exibido(
                        texto
                    )
                )

                if not validar_precos(
                    nome=nome,
                    preco_anterior=preco_anterior,
                    preco_atual=preco_atual,
                    desconto_exibido=desconto_exibido
                ):
                    continue

                # ==========================================
                # IMAGEM
                # ==========================================

                imagem = None

                img = card.locator(
                    "img"
                ).first

                if await img.count() > 0:
                    imagem = (
                        await img.get_attribute("src")
                        or await img.get_attribute(
                            "data-src"
                        )
                    )

                produto = {
                    "nome": nome,
                    "loja": "KaBuM!",
                    "preco_anterior": round(
                        preco_anterior,
                        2
                    ),
                    "preco_atual": round(
                        preco_atual,
                        2
                    ),
                    "url": url,
                    "imagem": imagem
                }

                produtos.append(produto)
                urls_processadas.add(url)

                desconto_calculado = (
                    (
                        preco_anterior
                        - preco_atual
                    )
                    / preco_anterior
                ) * 100

                print(
                    f"✅ {nome[:70]}"
                )

                print(
                    f"   R$ {preco_anterior:.2f}"
                    f" -> R$ {preco_atual:.2f}"
                    f" ({desconto_calculado:.2f}% OFF)"
                )

            except Exception as erro:
                print(
                    f"⚠️ Card {indice} ignorado: "
                    f"{erro}"
                )

        await browser.close()

    print("\n" + "-" * 60)

    print(
        f"📦 Ofertas válidas coletadas: "
        f"{len(produtos)}"
    )

    print("-" * 60)

    return produtos


URLS_KABUM_CATEGORIAS = [
    "https://www.kabum.com.br/hardware/placa-de-video-vga",
    "https://www.kabum.com.br/hardware/processadores",
    "https://www.kabum.com.br/hardware/memoria-ram",
    "https://www.kabum.com.br/hardware/placas-mae",
    "https://www.kabum.com.br/hardware/ssd-2-5",
    "https://www.kabum.com.br/hardware/fontes",
    "https://www.kabum.com.br/computadores/monitores",
]


async def buscar_ofertas_kabum_categorias(limite=60):
    """Páginas de listagem por categoria (cada card é o próprio link)."""

    from collectors.common import coletar_cards_playwright

    return await coletar_cards_playwright(
        loja="KaBuM!",
        url_pagina=URLS_KABUM_CATEGORIAS,
        base_url=BASE_URL,
        seletor_card='a[href*="/produto/"]',
        seletor_link=None,
        limite=limite,
        espera_ms=5000,
    )


async def buscar_ofertas_kabum(limite=20):
    """Vitrine de ofertas + categorias, sem repetir produtos."""

    produtos = await buscar_ofertas_kabum_vitrine(limite=limite)

    vistos = {p["url"] for p in produtos}

    if len(produtos) < limite:
        extras = await buscar_ofertas_kabum_categorias(
            limite=limite - len(produtos)
        )

        produtos += [p for p in extras if p["url"] not in vistos]

    return produtos[:limite]
