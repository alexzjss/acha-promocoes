import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    raise ValueError("ML_ACCESS_TOKEN não encontrado no .env")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

url = "https://api.mercadolibre.com/users/me"

resposta = requests.get(
    url,
    headers=headers,
    timeout=30
)

print("Status:", resposta.status_code)

if resposta.ok:
    dados = resposta.json()

    print("✅ TOKEN FUNCIONANDO")
    print("ID:", dados.get("id"))
    print("Nickname:", dados.get("nickname"))

else:
    print("❌ ERRO")
    print(resposta.text)