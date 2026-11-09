from collectors.common import coletar_cards_playwright


URL_PICHAU = "https://www.pichau.com.br/hardware"
BASE_URL = "https://www.pichau.com.br"


async def buscar_ofertas_pichau(limite=20):
    return await coletar_cards_playwright(
        loja="Pichau",
        url_pagina=URL_PICHAU,
        base_url=BASE_URL,
        seletor_card='a[data-cy="list-product"]',
        seletor_link=None,
        limite=limite,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(buscar_ofertas_pichau(limite=10))
