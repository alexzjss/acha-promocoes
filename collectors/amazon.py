from collectors.common import coletar_cards_playwright


URL_AMAZON = "https://www.amazon.com.br/blackfriday"
BASE_URL = "https://www.amazon.com.br"


async def buscar_ofertas_amazon(limite=20):
    # A Amazon tem anti-bot agressivo: se a página vier com CAPTCHA,
    # nenhum card é encontrado e o coletor retorna lista vazia.
    return await coletar_cards_playwright(
        loja="Amazon",
        url_pagina=URL_AMAZON,
        base_url=BASE_URL,
        seletor_card='div.dcl-product',
        seletor_link='a[href*="/dp/"]',
        seletor_nome=".dcl-product-title",
        limite=limite,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(buscar_ofertas_amazon(limite=10))
