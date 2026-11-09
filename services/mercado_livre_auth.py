import os
import requests

from dotenv import load_dotenv, set_key


load_dotenv()


ENV_FILE = ".env"

CLIENT_ID = os.getenv("ML_CLIENT_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")

ACCESS_TOKEN = os.getenv("ML_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN")

TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
USER_URL = "https://api.mercadolibre.com/users/me"


def validar_configuracao():
    """
    Verifica se as credenciais básicas existem.
    """

    campos = {
        "ML_CLIENT_ID": CLIENT_ID,
        "ML_CLIENT_SECRET": CLIENT_SECRET,
        "ML_REFRESH_TOKEN": REFRESH_TOKEN
    }

    faltando = [
        nome
        for nome, valor in campos.items()
        if not valor
    ]

    if faltando:
        print(
            "❌ Configuração incompleta do Mercado Livre."
        )

        for campo in faltando:
            print(f"   - {campo}")

        return False

    return True


def salvar_tokens(access_token, refresh_token):
    """
    Salva os tokens atualizados no .env local.
    """

    if access_token:
        set_key(
            ENV_FILE,
            "ML_ACCESS_TOKEN",
            access_token
        )

    if refresh_token:
        set_key(
            ENV_FILE,
            "ML_REFRESH_TOKEN",
            refresh_token
        )

    # Atualiza também o processo atual
    os.environ["ML_ACCESS_TOKEN"] = access_token

    if refresh_token:
        os.environ["ML_REFRESH_TOKEN"] = refresh_token


def renovar_access_token():
    """
    Usa o Refresh Token para gerar
    um novo Access Token.
    """

    if not validar_configuracao():
        return None

    print(
        "🔄 Renovando Access Token "
        "do Mercado Livre..."
    )

    dados = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": os.getenv(
            "ML_REFRESH_TOKEN"
        )
    }

    headers = {
        "accept": "application/json",
        "content-type":
            "application/x-www-form-urlencoded"
    }

    try:
        resposta = requests.post(
            TOKEN_URL,
            data=dados,
            headers=headers,
            timeout=30
        )

    except requests.RequestException as erro:

        print(
            "❌ Erro conectando ao Mercado Livre:"
        )

        print(erro)

        return None

    if resposta.status_code != 200:

        print(
            f"❌ Falha renovando token. "
            f"HTTP {resposta.status_code}"
        )

        try:
            erro = resposta.json()

            print(
                f"Erro: "
                f"{erro.get('error')}"
            )

            print(
                f"Mensagem: "
                f"{erro.get('message')}"
            )

        except ValueError:
            print(resposta.text)

        return None

    dados_token = resposta.json()

    novo_access_token = dados_token.get(
        "access_token"
    )

    novo_refresh_token = dados_token.get(
        "refresh_token"
    )

    if not novo_access_token:

        print(
            "❌ Access Token não veio "
            "na resposta."
        )

        return None

    salvar_tokens(
        novo_access_token,
        novo_refresh_token
    )

    print(
        "✅ Access Token renovado."
    )

    if novo_refresh_token:
        print(
            "✅ Refresh Token atualizado."
        )

    return novo_access_token


def testar_access_token(token):
    """
    Testa o token usando /users/me.
    """

    if not token:
        return False

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        resposta = requests.get(
            USER_URL,
            headers=headers,
            timeout=20
        )

    except requests.RequestException as erro:

        print(
            f"❌ Erro validando token: {erro}"
        )

        return False

    if resposta.status_code == 200:

        print(
            "✅ Access Token válido."
        )

        return True

    if resposta.status_code == 401:

        print(
            "⚠️ Access Token expirado "
            "ou inválido."
        )

        return False

    print(
        f"⚠️ /users/me retornou "
        f"HTTP {resposta.status_code}"
    )

    return False


def obter_access_token():
    """
    Função principal utilizada pelos collectors.

    1. Tenta usar o Access Token atual.
    2. Se não for válido, usa o Refresh Token.
    3. Retorna um token válido ou None.
    """

    token = os.getenv(
        "ML_ACCESS_TOKEN"
    )

    if token:

        print(
            "🔐 Verificando Access Token "
            "do Mercado Livre..."
        )

        if testar_access_token(token):
            return token

    print(
        "🔄 Necessário renovar "
        "o Access Token."
    )

    novo_token = renovar_access_token()

    if not novo_token:
        print(
            "❌ Não foi possível obter "
            "um Access Token válido."
        )

        return None

    return novo_token


if __name__ == "__main__":

    print(
        "\n🧪 TESTE DA AUTENTICAÇÃO "
        "DO MERCADO LIVRE"
    )

    print("=" * 60)

    token = obter_access_token()

    if token:

        print(
            "\n✅ AUTENTICAÇÃO FUNCIONANDO."
        )

    else:

        print(
            "\n❌ AUTENTICAÇÃO FALHOU."
        )