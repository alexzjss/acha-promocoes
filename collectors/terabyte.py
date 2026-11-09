from collectors.common import coletar_cards_playwright


URL_TERABYTE = [
    "https://www.terabyteshop.com.br/promocoes",
    "https://www.terabyteshop.com.br/promocoes?pagina=2",
    "https://www.terabyteshop.com.br/promocoes?pagina=3",
    "https://www.terabyteshop.com.br/hardware/placas-de-video",
    "https://www.terabyteshop.com.br/hardware/processadores",
]
BASE_URL = "https://www.terabyteshop.com.br"


async def buscar_ofertas_terabyte(limite=20):
    return await coletar_cards_playwright(
        loja="Terabyte",
        url_pagina=URL_TERABYTE,
        base_url=BASE_URL,
        seletor_card="div.product-item",
        seletor_link='a[href*="/produto/"]',
        limite=limite,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(buscar_ofertas_terabyte(limite=10))
