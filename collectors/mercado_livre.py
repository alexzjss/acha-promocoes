import os
import requests

from dotenv import load_dotenv


load_dotenv()

ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

BASE_URL = "https://api.mercadolibre.com"


def consultar_itens_vendedor(seller_id, limite=20):
    if not ACCESS_TOKEN:
        raise ValueError(
            "ML_ACCESS_TOKEN não encontrado no arquivo .env"
        )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    url = (
        f"{BASE_URL}/users/"
        f"{seller_id}/items/search"
    )

    resposta = requests.get(
        url,
        headers=headers,
        params={
            "status": "active",
            "limit": limite
        },
        timeout=30
    )

    print(
        f"🌐 Lista do vendedor {seller_id}: "
        f"{resposta.status_code}"
    )

    if not resposta.ok:
        print(resposta.text)
        return []

    dados = resposta.json()

    return dados.get("results", [])


def consultar_detalhes_itens(ids):
    if not ids:
        return []

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    url = f"{BASE_URL}/items/bulk"

    resposta = requests.get(
        url,
        headers=headers,
        params={
            "ids": ",".join(ids)
        },
        timeout=30
    )

    print(
        f"🌐 Detalhes dos itens: "
        f"{resposta.status_code}"
    )

    if not resposta.ok:
        print(resposta.text)
        return []

    return resposta.json()


def normalizar_produto(item):
    body = item.get("body", item)

    preco_atual = body.get("price")
    preco_anterior = body.get("original_price")

    if preco_atual is None:
        return None

    if preco_anterior is None:
        preco_anterior = preco_atual

    imagem = body.get("thumbnail")

    if imagem:
        imagem = imagem.replace(
            "http://",
            "https://"
        )

    return {
        "id_externo": body.get("id"),
        "nome": body.get(
            "title",
            "Produto sem nome"
        ),
        "loja": "Mercado Livre",
        "preco_anterior": float(preco_anterior),
        "preco_atual": float(preco_atual),
        "url": body.get("permalink"),
        "imagem": imagem
    }


def buscar_ofertas_vendedores(seller_ids):
    produtos = []

    for seller_id in seller_ids:
        try:
            ids = consultar_itens_vendedor(
                seller_id
            )

            detalhes = consultar_detalhes_itens(
                ids
            )

            for item in detalhes:
                produto = normalizar_produto(item)

                if produto is None:
                    continue

                if not produto["url"]:
                    continue

                produtos.append(produto)

        except Exception as erro:
            print(
                f"❌ Erro no vendedor "
                f"{seller_id}: {erro}"
            )

    print(
        f"📦 Total coletado no "
        f"Mercado Livre: {len(produtos)}"
    )

    return produtos