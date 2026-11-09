from collectors.common import coletar_cards_playwright


URL_PICHAU = [
    "https://www.pichau.com.br/hardware",
    "https://www.pichau.com.br/hardware?page=2",
    "https://www.pichau.com.br/hardware?page=3",
    "https://www.pichau.com.br/hardware/placa-de-video",
    "https://www.pichau.com.br/hardware/processadores",
]
BASE_URL = "https://www.pichau.com.br"


async def buscar_ofertas_pichau(limite=20):
    return await coletar_cards_playwright(
        loja="Pichau",
        url_pagina=URL_PICHAU,
        base_url=BASE_URL,
        seletor_card='a[data-cy="list-product"]',
        seletor_link=None,
        limite=limite,
        pausa_entre_paginas_s=8,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(buscar_ofertas_pichau(limite=10))
