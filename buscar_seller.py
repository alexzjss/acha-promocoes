import os
import requests

from dotenv import load_dotenv


load_dotenv()

ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

BASE_URL = "https://api.mercadolibre.com"


def buscar_vendedor(nickname):
    if not ACCESS_TOKEN:
        raise ValueError(
            "ML_ACCESS_TOKEN não encontrado no arquivo .env"
        )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    url = f"{BASE_URL}/sites/MLB/search"

    params = {
        "nickname": nickname,
        "limit": 1
    }

    print("\n" + "=" * 60)
    print(f"🔎 Buscando vendedor: {nickname}")
    print("=" * 60)

    try:
        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

    except requests.RequestException as erro:
        print(
            f"❌ Erro de conexão: {erro}"
        )
        return None

    print(
        f"🌐 Status da API: "
        f"{resposta.status_code}"
    )

    if resposta.status_code == 401:
        print(
            "❌ Access Token inválido ou expirado."
        )
        return None

    if resposta.status_code == 403:
        print(
            "❌ A API recusou essa busca com 403."
        )

        print(
            "O token pode estar válido, mas esse "
            "recurso pode estar restrito para a aplicação."
        )

        return None

    if not resposta.ok:
        print(
            "❌ Erro retornado pela API:"
        )

        print(resposta.text)

        return None

    dados = resposta.json()

    resultados = dados.get(
        "results",
        []
    )

    if not resultados:
        print(
            f"⚠️ Nenhum anúncio encontrado "
            f"para {nickname}."
        )

        return None

    primeiro_item = resultados[0]

    vendedor = primeiro_item.get(
        "seller",
        {}
    )

    seller_id = vendedor.get("id")

    seller_nickname = vendedor.get(
        "nickname"
    )

    if not seller_id:
        print(
            "⚠️ A API retornou um produto, "
            "mas não informou o Seller ID."
        )

        return None

    print("\n✅ VENDEDOR ENCONTRADO")

    print(
        f"🏪 Nickname: "
        f"{seller_nickname}"
    )

    print(
        f"🆔 Seller ID: "
        f"{seller_id}"
    )

    print(
        f"📦 Produto usado para validação: "
        f"{primeiro_item.get('title')}"
    )

    return {
        "nickname": seller_nickname,
        "seller_id": seller_id
    }


def main():
    print("\n" + "=" * 60)
    print("🤖 ACHA-PROMOÇÕES")
    print("🔎 BUSCADOR DE SELLER IDs")
    print("=" * 60)

    vendedores = []

    while True:
        nickname = input(
            "\nDigite o nickname da loja "
            "(ou 'sair'): "
        ).strip()

        if nickname.lower() == "sair":
            break

        if not nickname:
            print(
                "⚠️ Digite um nickname válido."
            )
            continue

        resultado = buscar_vendedor(
            nickname
        )

        if resultado:
            vendedores.append(
                resultado
            )

    print("\n" + "=" * 60)
    print("📋 VENDEDORES ENCONTRADOS")
    print("=" * 60)

    if not vendedores:
        print(
            "Nenhum Seller ID foi encontrado."
        )

        return

    ids = []

    for vendedor in vendedores:
        print(
            f"🏪 {vendedor['nickname']} "
            f"→ {vendedor['seller_id']}"
        )

        ids.append(
            str(vendedor["seller_id"])
        )

    print("\n✅ LINHA PARA O .env:\n")

    print(
        "ML_SELLER_IDS="
        + ",".join(ids)
    )


if __name__ == "__main__":
    main()