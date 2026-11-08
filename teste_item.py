import os
import requests

from dotenv import load_dotenv


load_dotenv()

ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

ITEM_ID = "MLB6889676920"

URL = "https://api.mercadolibre.com/items/bulk"


if not ACCESS_TOKEN:
    raise ValueError(
        "ML_ACCESS_TOKEN não encontrado no .env"
    )


headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

params = {
    "ids": ITEM_ID
}


print("=" * 60)
print("🔎 TESTANDO ITEM REAL DO MERCADO LIVRE")
print("=" * 60)

print(f"Item ID: {ITEM_ID}")


try:
    resposta = requests.get(
        URL,
        headers=headers,
        params=params,
        timeout=30
    )

except requests.RequestException as erro:
    print(f"❌ Erro de conexão: {erro}")
    raise SystemExit


print(f"\n🌐 Status da API: {resposta.status_code}")


if resposta.status_code == 401:
    print("❌ Access Token inválido ou expirado.")
    raise SystemExit


if resposta.status_code == 403:
    print("❌ O Mercado Livre bloqueou este recurso com 403.")
    raise SystemExit


if not resposta.ok:
    print("❌ Erro retornado pela API:")
    print(resposta.text)
    raise SystemExit


dados = resposta.json()


import json

print("\n✅ API RESPONDEU COM SUCESSO")

print("\n🔎 RESPOSTA COMPLETA DA API")
print("=" * 60)

print(
    json.dumps(
        dados,
        indent=2,
        ensure_ascii=False
    )
)