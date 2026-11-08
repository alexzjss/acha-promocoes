import os
import hashlib
import base64
import secrets
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv


load_dotenv()

CLIENT_ID = os.getenv("ML_CLIENT_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ML_REDIRECT_URI")


if not CLIENT_ID:
    raise ValueError("ML_CLIENT_ID não encontrado no .env")

if not CLIENT_SECRET:
    raise ValueError("ML_CLIENT_SECRET não encontrado no .env")

if not REDIRECT_URI:
    raise ValueError("ML_REDIRECT_URI não encontrado no .env")


# ==========================================
# 1. GERAR PKCE
# ==========================================

code_verifier = secrets.token_urlsafe(64)

challenge = hashlib.sha256(
    code_verifier.encode()
).digest()

code_challenge = (
    base64.urlsafe_b64encode(challenge)
    .decode()
    .rstrip("=")
)


# ==========================================
# 2. GERAR URL DE AUTORIZAÇÃO
# ==========================================

params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "code_challenge": code_challenge,
    "code_challenge_method": "S256"
}

url_autorizacao = (
    "https://auth.mercadolivre.com.br/authorization?"
    + urlencode(params)
)

print("\n==========================================")
print("🔐 AUTORIZAÇÃO MERCADO LIVRE")
print("==========================================")

print("\nAbra esta URL no navegador:\n")

print(url_autorizacao)

print("\n⚠️ Não feche este terminal.")


# ==========================================
# 3. RECEBER AUTHORIZATION CODE
# ==========================================

authorization_code = input(
    "\nCole aqui somente o CODE recebido na URL: "
).strip()


# ==========================================
# 4. TROCAR CODE PELO ACCESS TOKEN
# ==========================================

token_url = "https://api.mercadolibre.com/oauth/token"

dados = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": authorization_code,
    "redirect_uri": REDIRECT_URI,
    "code_verifier": code_verifier
}

resposta = requests.post(
    token_url,
    data=dados,
    timeout=30
)

print("\n==========================================")
print(f"Status: {resposta.status_code}")
print("==========================================")


# ==========================================
# 5. RESULTADO
# ==========================================

if resposta.ok:

    token_data = resposta.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    print("\n✅ ACCESS TOKEN GERADO!")
    

    print("\nRefresh Token recebido:")
    print(bool(refresh_token))

    print("\nExpira em:")
    print(expires_in)

    print(
        "\n⚠️ Copie o Access Token para o .env "
        "e depois feche este terminal."
    )

else:

    print("\n❌ ERRO AO GERAR ACCESS TOKEN")
    print(resposta.text)