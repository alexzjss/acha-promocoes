from collectors.common import coletar_cards_playwright


URL_MAGALU = "https://www.magazineluiza.com.br/selecao/ofertasdodia/"
BASE_URL = "https://www.magazineluiza.com.br"


async def buscar_ofertas_magalu(limite=20):
    return await coletar_cards_playwright(
        loja="Magalu",
        url_pagina=URL_MAGALU,
        base_url=BASE_URL,
        seletor_card='div[data-testid="product-card-container"]',
        seletor_link='a[data-testid="product-card-link"]',
        limite=limite,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(buscar_ofertas_magalu(limite=10))
