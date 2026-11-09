import os
import secrets
import hashlib
import base64

from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv, set_key


# ============================================================
# CAMINHO FIXO DO .ENV
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


# ============================================================
# CONFIGURAÇÃO MERCADO LIVRE
# ============================================================

CLIENT_ID = os.getenv("ML_CLIENT_ID")
REDIRECT_URI = os.getenv("ML_REDIRECT_URI")
OAUTH_STATE = os.getenv("ML_OAUTH_STATE")


AUTH_URL = (
    "https://auth.mercadolivre.com.br/authorization"
)


# ============================================================
# GERAR CODE VERIFIER
# ============================================================

def gerar_code_verifier():
    """
    Gera o code_verifier usado pelo PKCE.
    """

    return secrets.token_urlsafe(64)


# ============================================================
# GERAR CODE CHALLENGE
# ============================================================

def gerar_code_challenge(code_verifier):
    """
    Gera code_challenge SHA256 a partir
    do code_verifier.
    """

    digest = hashlib.sha256(
        code_verifier.encode("utf-8")
    ).digest()

    challenge = base64.urlsafe_b64encode(
        digest
    ).decode("utf-8")

    return challenge.rstrip("=")


# ============================================================
# VALIDAR CONFIGURAÇÃO
# ============================================================

def validar_configuracao():

    campos = {
        "ML_CLIENT_ID": CLIENT_ID,
        "ML_REDIRECT_URI": REDIRECT_URI,
        "ML_OAUTH_STATE": OAUTH_STATE
    }

    faltando = []

    for nome, valor in campos.items():

        if not valor:
            faltando.append(nome)

    if faltando:

        print("\n❌ Variáveis ausentes no .env:")

        for campo in faltando:
            print(f"   - {campo}")

        print(
            f"\n📁 .env utilizado: {ENV_FILE}"
        )

        return False

    print("\n✅ Configuração carregada:")

    print("   ML_CLIENT_ID: OK")
    print("   ML_REDIRECT_URI: OK")
    print("   ML_OAUTH_STATE: OK")

    print(
        f"\n📁 .env utilizado: {ENV_FILE}"
    )

    return True


# ============================================================
# SALVAR CODE VERIFIER
# ============================================================

def salvar_code_verifier(code_verifier):

    try:

        set_key(
            str(ENV_FILE),
            "ML_CODE_VERIFIER",
            code_verifier
        )

        # Atualiza também o processo atual
        os.environ[
            "ML_CODE_VERIFIER"
        ] = code_verifier

    except Exception as erro:

        print(
            "\n❌ Erro salvando ML_CODE_VERIFIER:"
        )

        print(erro)

        return False

    print(
        "\n💾 ML_CODE_VERIFIER salvo no .env."
    )

    print(
        f"📏 Tamanho: "
        f"{len(code_verifier)} caracteres"
    )

    return True


# ============================================================
# GERAR URL DE AUTORIZAÇÃO
# ============================================================

def gerar_url_autorizacao():

    print(
        "\n🔐 MERCADO LIVRE OAUTH + PKCE"
    )

    print("=" * 70)

    if not validar_configuracao():
        return

    # --------------------------------------------------------
    # GERAR PKCE
    # --------------------------------------------------------

    code_verifier = gerar_code_verifier()

    code_challenge = gerar_code_challenge(
        code_verifier
    )

    # --------------------------------------------------------
    # SALVAR VERIFIER
    # --------------------------------------------------------

    if not salvar_code_verifier(
        code_verifier
    ):
        return

    # --------------------------------------------------------
    # PARÂMETROS OAUTH
    # --------------------------------------------------------

    parametros = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "state": OAUTH_STATE,

        # PKCE
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    # --------------------------------------------------------
    # GERAR URL
    # --------------------------------------------------------

    url = (
        f"{AUTH_URL}?"
        f"{urlencode(parametros)}"
    )

    print("\n" + "=" * 70)

    print(
        "\n✅ PKCE gerado com sucesso."
    )

    print(
        "✅ Code Verifier salvo no .env correto."
    )

    print(
        "\n🌐 Abra a URL abaixo no navegador:\n"
    )

    print(url)

    print("\n" + "=" * 70)

    print(
        "\n📡 Após autorizar, "
        "o Mercado Livre deverá redirecionar para:"
    )

    print(
        f"\n{REDIRECT_URI}"
    )

    print(
        "\n⚠️ IMPORTANTE:"
    )

    print(
        "Não execute gerar_oauth_ml.py novamente "
        "antes de trocar o code pelo token."
    )

    print(
        "Executar novamente gera outro "
        "ML_CODE_VERIFIER."
    )

    print(
        "\nDepois de receber o novo code, execute:"
    )

    print(
        "\npython trocar_token_ml.py"
    )

    print("\n" + "=" * 70)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    gerar_url_autorizacao()