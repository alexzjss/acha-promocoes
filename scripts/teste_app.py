import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")
APP_ID = os.getenv("ML_CLIENT_ID")

if not ACCESS_TOKEN:
    raise ValueError("ML_ACCESS_TOKEN não encontrado no .env")

if not APP_ID:
    raise ValueError("ML_CLIENT_ID não encontrado no .env")

url = f"https://api.mercadolibre.com/applications/{APP_ID}"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

resposta = requests.get(
    url,
    headers=headers,
    timeout=30
)

print("Status:", resposta.status_code)

if resposta.ok:
    dados = resposta.json()

    print("\n✅ APLICAÇÃO ENCONTRADA")
    print("ID:", dados.get("id"))
    print("Site:", dados.get("site_id"))
    print("Ativa:", dados.get("active"))
    print("Sandbox:", dados.get("sandbox_mode"))
    print("Certificação:", dados.get("certification_status"))

    print("\nScopes:")
    print(dados.get("scopes"))

else:
    print("\n❌ ERRO")
    print(resposta.text)
    
    
    print("\n🔎 TESTANDO AUTORIZAÇÃO DO USUÁRIO...")

url_user = "https://api.mercadolibre.com/users/me"

resposta_user = requests.get(
    url_user,
    headers=headers,
    timeout=30
)

if resposta_user.ok:
    usuario = resposta_user.json()
    USER_ID = usuario.get("id")

    url_apps = (
        f"https://api.mercadolibre.com/users/{USER_ID}/applications"
    )

    resposta_apps = requests.get(
        url_apps,
        headers=headers,
        timeout=30
    )

    print("Status autorizações:", resposta_apps.status_code)

    if resposta_apps.ok:
        apps = resposta_apps.json()

        for app in apps:
            if str(app.get("app_id")) == str(APP_ID):
                print("✅ Autorização encontrada")
                print("Scopes concedidos:", app.get("scopes"))
    else:
        print(resposta_apps.text)