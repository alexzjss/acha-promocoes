from urllib.parse import quote_plus

from collectors.common import coletar_cards_playwright
from services.category_classifier import identificar_categoria


BASE_URL = "https://www.amazon.com.br"

# A vitrine de ofertas é geral (mercado, beleza...); as buscas por
# termo trazem o nicho de hardware com preço "de/por".
URL_VITRINE = f"{BASE_URL}/blackfriday"

TERMOS_BUSCA = [
    "placa de video rtx",
    "placa de video radeon",
    "processador ryzen",
    "processador intel core",
    "ssd nvme",
    "memoria ram ddr5",
    "monitor gamer",
    "fonte 80 plus",
    "gabinete gamer",
    "water cooler",
]

URL_AMAZON = [URL_VITRINE] + [
    f"{BASE_URL}/s?k={quote_plus(t)}&i=computers" for t in TERMOS_BUSCA
]


async def buscar_ofertas_amazon(limite=20):
    produtos = await coletar_cards_playwright(
        loja="Amazon",
        url_pagina=URL_AMAZON,
        base_url=BASE_URL,
        seletor_card=(
            'div.dcl-product, '
            'div[data-component-type="s-search-result"]'
        ),
        seletor_link='a[href*="/dp/"]',
        seletor_nome="h2, .dcl-product-title",
        limite=limite * 4,
        pausa_entre_paginas_s=3,
    )

    # Mantém só itens que o classificador reconhece como do nicho.
    relevantes = [
        p for p in produtos
        if identificar_categoria(p["nome"]) != "outros"
    ]

    print(
        f"🎯 Amazon: {len(relevantes)} de {len(produtos)} "
        "ofertas são do nicho."
    )

    return relevantes[:limite]


if __name__ == "__main__":
    import asyncio

    asyncio.run(buscar_ofertas_amazon(limite=10))
