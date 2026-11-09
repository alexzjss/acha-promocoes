import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


URL_PICHAU = "https://www.pichau.com.br/hardware"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"
}


def converter_preco(texto):
    """
    Converte:
    R$ 3.529,40
    para:
    3529.40
    """

    if not texto:
        return None

    resultado = re.search(
        r"R\$\s*([\d\.]+,\d{2})",
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


def buscar_ofertas_pichau():
    """
    Busca ofertas da Pichau e retorna produtos
    no formato esperado pelo deal_processor.py.
    """

    produtos = []

    print("🔎 Buscando ofertas na Pichau...")

    try:
        resposta = requests.get(
            URL_PICHAU,
            headers=HEADERS,
            timeout=20
        )

    except requests.RequestException as erro:
        print(
            f"❌ Erro acessando Pichau: {erro}"
        )

        return produtos

    if resposta.status_code != 200:

        print(
            f"❌ Pichau retornou HTTP "
            f"{resposta.status_code}"
        )

        return produtos

    soup = BeautifulSoup(
        resposta.text,
        "html.parser"
    )

    # Procuramos links de produtos inicialmente.
    links = soup.find_all(
        "a",
        href=True
    )

    urls_encontradas = set()

    for link in links:

        href = link.get("href")

        if not href:
            continue

        # Evita processar o mesmo link várias vezes
        url = urljoin(
            "https://www.pichau.com.br",
            href
        )

        if url in urls_encontradas:
            continue

        texto = link.get_text(
            " ",
            strip=True
        )

        # Precisamos de preço para considerar
        # o elemento candidato a produto.
        if "R$" not in texto:
            continue

        # Tentamos encontrar padrão:
        # de R$ X por R$ Y
        precos = re.findall(
            r"R\$\s*[\d\.]+,\d{2}",
            texto
        )

        if len(precos) < 2:
            continue

        preco_anterior = converter_preco(
            precos[0]
        )

        preco_atual = converter_preco(
            precos[1]
        )

        if (
            preco_anterior is None
            or preco_atual is None
        ):
            continue

        # Segurança básica antes de enviar
        # para o pipeline principal
        if preco_atual >= preco_anterior:
            continue

        # Nome inicial
        nome = texto

        # Remove partes mais óbvias de preço
        nome = re.split(
            r"\bde\s+R\$",
            nome,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0].strip()

        if len(nome) < 5:
            continue

        # Procura imagem dentro do elemento
        imagem = None

        img = link.find("img")

        if img:
            imagem = (
                img.get("src")
                or img.get("data-src")
            )

            if imagem:
                imagem = urljoin(
                    "https://www.pichau.com.br",
                    imagem
                )

        produto = {
            "nome": nome,

            "loja": "Pichau",

            "preco_anterior": preco_anterior,

            "preco_atual": preco_atual,

            "url": url,

            "imagem": imagem
        }

        produtos.append(produto)

        urls_encontradas.add(url)

    print(
        f"✅ Pichau: "
        f"{len(produtos)} ofertas encontradas."
    )

    return produtos


# =========================================================
# TESTE ISOLADO
# =========================================================

if __name__ == "__main__":

    ofertas = buscar_ofertas_pichau()

    print("\n" + "=" * 70)
    print("🧪 TESTE DO COLETOR PICHAU")
    print("=" * 70)

    for indice, produto in enumerate(
        ofertas[:10],
        start=1
    ):

        print(
            f"\n📦 Produto #{indice}"
        )

        print(
            f"Nome: {produto['nome']}"
        )

        print(
            f"Loja: {produto['loja']}"
        )

        print(
            f"Anterior: "
            f"R$ {produto['preco_anterior']:.2f}"
        )

        print(
            f"Atual: "
            f"R$ {produto['preco_atual']:.2f}"
        )

        desconto = (
            (
                produto["preco_anterior"]
                - produto["preco_atual"]
            )
            / produto["preco_anterior"]
        ) * 100

        print(
            f"Desconto: "
            f"{desconto:.2f}%"
        )

        print(
            f"URL: {produto['url']}"
        )

        print(
            f"Imagem: {produto['imagem']}"
        )