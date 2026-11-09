import os
import requests

from dotenv import load_dotenv, set_key


# ============================================================
# CONFIGURAÇÃO
# ============================================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv()


CLIENT_ID = os.getenv("ML_CLIENT_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ML_REDIRECT_URI")
CODE_VERIFIER = os.getenv("ML_CODE_VERIFIER")

TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
USER_URL = "https://api.mercadolibre.com/users/me"


# ============================================================
# VALIDAR CONFIGURAÇÃO
# ============================================================

def validar_configuracao():

    campos = {
        "ML_CLIENT_ID": CLIENT_ID,
        "ML_CLIENT_SECRET": CLIENT_SECRET,
        "ML_REDIRECT_URI": REDIRECT_URI,
        "ML_CODE_VERIFIER": CODE_VERIFIER
    }

    faltando = []

    for nome, valor in campos.items():

        if not valor:
            faltando.append(nome)

    if faltando:

        print("\n❌ Variáveis ausentes no .env:")

        for campo in faltando:
            print(f"   - {campo}")

        return False

    print("\n✅ Configuração carregada:")
    print("   ML_CLIENT_ID: OK")
    print("   ML_CLIENT_SECRET: OK")
    print("   ML_REDIRECT_URI: OK")
    print("   ML_CODE_VERIFIER: OK")

    print(
        f"   Tamanho do CODE_VERIFIER: "
        f"{len(CODE_VERIFIER)} caracteres"
    )

    return True


# ============================================================
# TROCAR CODE POR TOKEN
# ============================================================

def trocar_code_por_token(code):

    dados = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,

        # PKCE
        "code_verifier": CODE_VERIFIER
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }

    print("\n🔄 Trocando código por token...")

    try:

        resposta = requests.post(
            TOKEN_URL,
            data=dados,
            headers=headers,
            timeout=30
        )

    except requests.RequestException as erro:

        print("\n❌ Erro conectando ao Mercado Livre:")
        print(erro)

        return None

    print(
        f"\n📡 HTTP {resposta.status_code}"
    )

    if resposta.status_code != 200:

        print(
            "\n❌ Mercado Livre recusou "
            "a troca do código."
        )

        try:

            erro = resposta.json()

            print(
                f"Erro: "
                f"{erro.get('error', 'desconhecido')}"
            )

            print(
                f"Mensagem: "
                f"{erro.get('message', 'sem mensagem')}"
            )

        except ValueError:

            print(resposta.text)

        return None

    try:

        return resposta.json()

    except ValueError:

        print(
            "\n❌ Mercado Livre retornou "
            "uma resposta inválida."
        )

        return None


# ============================================================
# SALVAR TOKENS NO .ENV
# ============================================================

def salvar_tokens(access_token, refresh_token):

    if not access_token:

        print(
            "\n❌ Access Token ausente."
        )

        return False

    try:

        set_key(
    str(ENV_FILE),
    "ML_ACCESS_TOKEN",
    access_token
)

        if refresh_token:

            set_key(
                ENV_FILE,
                "ML_REFRESH_TOKEN",
                refresh_token
            )

        # Atualiza também as variáveis do processo atual
        os.environ["ML_ACCESS_TOKEN"] = access_token

        if refresh_token:

            os.environ[
                "ML_REFRESH_TOKEN"
            ] = refresh_token

    except Exception as erro:

        print(
            "\n❌ Erro salvando tokens no .env:"
        )

        print(erro)

        return False

    print(
        "\n💾 Tokens salvos no .env."
    )

    print(
        "🔐 Access Token armazenado."
    )

    if refresh_token:

        print(
            "🔄 Refresh Token armazenado."
        )

    return True


# ============================================================
# TESTAR TOKEN
# ============================================================

def testar_token(access_token):

    print(
        "\n🧪 Testando Access Token "
        "em /users/me..."
    )

    headers = {
        "Authorization":
            f"Bearer {access_token}"
    }

    try:

        resposta = requests.get(
            USER_URL,
            headers=headers,
            timeout=30
        )

    except requests.RequestException as erro:

        print(
            f"\n❌ Erro testando token: {erro}"
        )

        return False

    print(
        f"📡 /users/me → "
        f"HTTP {resposta.status_code}"
    )

    if resposta.status_code != 200:

        print(
            "❌ Access Token não foi aceito."
        )

        return False

    try:

        usuario = resposta.json()

    except ValueError:

        print(
            "❌ Resposta inválida em /users/me."
        )

        return False

    print(
        "\n✅ ACCESS TOKEN FUNCIONANDO!"
    )

    print(
        f"👤 User ID: "
        f"{usuario.get('id')}"
    )

    print(
        f"👤 Nickname: "
        f"{usuario.get('nickname')}"
    )

    return True


# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    print(
        "\n🔐 MERCADO LIVRE OAUTH + PKCE"
    )

    print("=" * 60)

    if not validar_configuracao():
        return

    print(
        "\nCole o NOVO code recebido "
        "pelo callback do Render."
    )

    print(
        "🔒 O code não será armazenado."
    )

    code = input(
        "\nCode: "
    ).strip()

    if not code:

        print(
            "\n❌ Nenhum code informado."
        )

        return

    resultado = trocar_code_por_token(
        code
    )

    if not resultado:
        return

    access_token = resultado.get(
        "access_token"
    )

    refresh_token = resultado.get(
        "refresh_token"
    )

    expires_in = resultado.get(
        "expires_in"
    )

    user_id = resultado.get(
        "user_id"
    )

    if not access_token:

        print(
            "\n❌ A resposta não contém "
            "Access Token."
        )

        return

    print("\n" + "=" * 60)

    print(
        "✅ TOKEN RECEBIDO DO MERCADO LIVRE"
    )

    print("=" * 60)

    if user_id:

        print(
            f"\n👤 User ID: {user_id}"
        )

    if expires_in:

        print(
            f"⏱️ Expiração: "
            f"{expires_in} segundos"
        )

    print(
        "\n🔐 Access Token: recebido"
    )

    if refresh_token:

        print(
            "🔄 Refresh Token: recebido"
        )

    print(
        "\n⚠️ Os valores dos tokens "
        "não serão exibidos."
    )

    # ========================================================
    # SALVAR
    # ========================================================

    salvo = salvar_tokens(
        access_token,
        refresh_token
    )

    if not salvo:
        return

    # ========================================================
    # TESTAR
    # ========================================================

    token_valido = testar_token(
        access_token
    )

    print("\n" + "=" * 60)

    if token_valido:

        print(
            "🔥 MERCADO LIVRE "
            "AUTENTICADO COM SUCESSO!"
        )

        print(
            "✅ Tokens armazenados "
            "no .env local."
        )

    else:

        print(
            "⚠️ Tokens foram recebidos, "
            "mas o teste da API falhou."
        )

    print("=" * 60)


if __name__ == "__main__":
    main()