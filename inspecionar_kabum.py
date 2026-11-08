import asyncio

from playwright.async_api import async_playwright


URL_KABUM = "https://www.kabum.com.br/ofertas"


async def main():
    print("=" * 70)
    print("🔬 INSPECIONADOR KABUM")
    print("=" * 70)

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

        print("\n🌐 Abrindo KaBuM!...")

        try:
            resposta = await page.goto(
                URL_KABUM,
                wait_until="domcontentloaded",
                timeout=60000
            )

        except Exception as erro:
            print(
                f"❌ Erro ao abrir a KaBuM!: {erro}"
            )

            await browser.close()
            return

        if resposta:
            print(
                f"🌐 HTTP: {resposta.status}"
            )

        # Aguarda os produtos carregarem
        await page.wait_for_timeout(5000)

        print(
            f"📄 Título: {await page.title()}"
        )

        # =====================================================
        # ENCONTRAR PRODUTOS
        # =====================================================

        links = page.locator(
            'a[href*="/produto/"]'
        )

        quantidade = await links.count()

        print(
            f"🔎 Links de produtos: {quantidade}"
        )

        if quantidade == 0:
            print(
                "❌ Nenhum link de produto encontrado."
            )

            await browser.close()
            return

        # =====================================================
        # PRIMEIRO PRODUTO
        # =====================================================

        link = links.first

        href = await link.get_attribute(
            "href"
        )

        print("\n" + "=" * 70)
        print("🔗 PRIMEIRO PRODUTO")
        print("=" * 70)

        print(href)

        # =====================================================
        # LOCALIZAR CARROSSEL
        # =====================================================

        elementos = await link.evaluate(
            """
            element => {

                let container = element.closest(
                    '#carousel-justArrived'
                );

                if (!container) {

                    container = element.closest(
                        '[id*="carousel"]'
                    );

                }

                if (!container) {

                    return {
                        encontrado: false,
                        elementos: []
                    };

                }

                const todos =
                    container.querySelectorAll("*");

                const resultado = [];

                for (const el of todos) {

                    const texto =
                        (el.innerText || "")
                        .trim();

                    const tag =
                        el.tagName;

                    const classe =
                        typeof el.className === "string"
                            ? el.className
                            : "";

                    const temPreco =
                        texto.includes("R$");

                    const temDesconto =
                        /-?\\d+\\s*%/.test(texto);

                    const ehImagem =
                        tag === "IMG";

                    const ehTitulo =
                        (
                            tag === "H1" ||
                            tag === "H2" ||
                            tag === "H3" ||
                            tag === "H4"
                        );

                    if (
                        temPreco ||
                        temDesconto ||
                        ehImagem ||
                        ehTitulo
                    ) {

                        resultado.push({

                            tag: tag,

                            classe: classe,

                            id:
                                el.id || "",

                            texto:
                                texto.substring(
                                    0,
                                    600
                                ),

                            src:
                                tag === "IMG"
                                    ? (
                                        el.src ||
                                        el.getAttribute(
                                            "data-src"
                                        ) ||
                                        ""
                                    )
                                    : ""
                        });

                    }

                }

                return {
                    encontrado: true,
                    elementos: resultado.slice(
                        0,
                        120
                    )
                };
            }
            """
        )

        # =====================================================
        # RESULTADO
        # =====================================================

        if not elementos["encontrado"]:

            print(
                "\n❌ Nenhum carrossel relacionado "
                "ao produto foi encontrado."
            )

            await browser.close()
            return

        lista = elementos[
            "elementos"
        ]

        print("\n" + "=" * 70)
        print("🔬 ELEMENTOS INTERNOS DO CARROSSEL")
        print("=" * 70)

        print(
            f"Elementos relevantes: "
            f"{len(lista)}"
        )

        for indice, elemento in enumerate(
            lista,
            start=1
        ):

            print("\n" + "-" * 70)

            print(
                f"[{indice}]"
            )

            print(
                f"TAG: "
                f"{elemento['tag']}"
            )

            print(
                f"ID: "
                f"{elemento['id']}"
            )

            print(
                f"CLASSE: "
                f"{elemento['classe']}"
            )

            if elemento[
                "texto"
            ]:

                print("TEXTO:")

                print(
                    elemento["texto"]
                )

            if elemento[
                "src"
            ]:

                print(
                    f"IMAGEM: "
                    f"{elemento['src']}"
                )

        # =====================================================
        # ELEMENTOS QUE CONTÊM SOMENTE UM PREÇO
        # =====================================================

        precos = await link.evaluate(
            """
            element => {

                let container =
                    element.closest(
                        '#carousel-justArrived'
                    );

                if (!container) {

                    container =
                        element.closest(
                            '[id*="carousel"]'
                        );

                }

                if (!container) {
                    return [];
                }

                const todos =
                    container.querySelectorAll("*");

                const resultado = [];

                for (const el of todos) {

                    const texto =
                        (el.innerText || "")
                        .trim();

                    const ocorrencias =
                        texto.match(
                            /R\\$\\s*[\\d.]+,\\d{2}/g
                        );

                    if (
                        ocorrencias &&
                        ocorrencias.length === 1 &&
                        texto.length < 100
                    ) {

                        resultado.push({

                            tag:
                                el.tagName,

                            classe:
                                typeof el.className
                                    === "string"
                                    ? el.className
                                    : "",

                            texto:
                                texto
                        });

                    }

                }

                return resultado.slice(
                    0,
                    80
                );
            }
            """
        )

        print("\n" + "=" * 70)
        print("💰 CANDIDATOS A ELEMENTOS DE PREÇO")
        print("=" * 70)

        for indice, preco in enumerate(
            precos,
            start=1
        ):

            print(
                f"\n[{indice}]"
            )

            print(
                f"TAG: {preco['tag']}"
            )

            print(
                f"CLASSE: {preco['classe']}"
            )

            print(
                f"TEXTO: {preco['texto']}"
            )

        print("\n" + "=" * 70)
        print("✅ INSPEÇÃO CONCLUÍDA")
        print("=" * 70)

        await browser.close()


if __name__ == "__main__":

    asyncio.run(
        main()
    )