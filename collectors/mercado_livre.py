import sys
import time
from pathlib import Path

import requests


# ============================================================
# GARANTIR ACESSO À RAIZ DO PROJETO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from services.mercado_livre_auth import (
    obter_access_token,
    renovar_access_token
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

SITE_ID = "MLB"

API_BASE_URL = "https://api.mercadolibre.com"

SEARCH_URL = (
    f"{API_BASE_URL}/sites/{SITE_ID}/search"
)

TIMEOUT = 30

LIMITE_POR_BUSCA = 10

INTERVALO_REQUISICOES = 0.25


# Termos usados para encontrar produtos
# das categorias do seu Discord.

TERMOS_BUSCA = [
    "placa de video",
    "processador",
    "placa mae",
    "memoria ram",
    "ssd nvme",
    "fonte gamer",
    "water cooler",
    "cooler processador",
    "kit fan gabinete",
    "gabinete gamer",
    "monitor gamer",
    "suporte monitor",
    "mouse gamer",
    "teclado gamer",
    "headset gamer",
    "cadeira gamer",
    "action figure",
    "funko pop"
]


# ============================================================
# CRIAR SESSÃO HTTP
# ============================================================

def criar_sessao(access_token):

    sessao = requests.Session()

    sessao.headers.update(
        {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Accept": "application/json",
            "User-Agent": (
                "Acha-Promocoes/1.0 "
                "(Discord promotion bot)"
            )
        }
    )

    return sessao


# ============================================================
# NORMALIZAR IMAGEM
# ============================================================

def normalizar_imagem(url):

    if not url:
        return None

    if url.startswith("http://"):
        return url.replace(
            "http://",
            "https://",
            1
        )

    return url


# ============================================================
# VALIDAR VALOR
# ============================================================

def converter_numero(valor):

    if valor is None:
        return None

    try:
        return float(valor)

    except (TypeError, ValueError):
        return None


# ============================================================
# FAZER GET COM RENOVAÇÃO DE TOKEN
# ============================================================

def fazer_get(
    sessao,
    url,
    parametros=None
):
    """
    Executa uma requisição autenticada.

    Se receber HTTP 401:
    1. Renova o Access Token.
    2. Atualiza o header.
    3. Repete a requisição uma vez.
    """

    try:
        resposta = sessao.get(
            url,
            params=parametros,
            timeout=TIMEOUT
        )

    except requests.RequestException as erro:

        print(
            f"❌ Erro consultando Mercado Livre: "
            f"{erro}"
        )

        return None

    if resposta.status_code != 401:
        return resposta

    print(
        "⚠️ Mercado Livre retornou HTTP 401."
    )

    print(
        "🔄 Tentando renovar o Access Token..."
    )

    novo_token = renovar_access_token()

    if not novo_token:

        print(
            "❌ Não foi possível renovar "
            "o Access Token."
        )

        return resposta

    sessao.headers.update(
        {
            "Authorization": (
                f"Bearer {novo_token}"
            )
        }
    )

    try:
        return sessao.get(
            url,
            params=parametros,
            timeout=TIMEOUT
        )

    except requests.RequestException as erro:

        print(
            "❌ Erro repetindo requisição "
            f"ao Mercado Livre: {erro}"
        )

        return None


# ============================================================
# BUSCAR ITENS POR TERMO
# ============================================================

def buscar_itens_por_termo(
    sessao,
    termo,
    limite=LIMITE_POR_BUSCA
):
    """
    Busca anúncios no Mercado Livre
    utilizando palavras-chave.
    """

    parametros = {
        "q": termo,
        "limit": limite,
        "offset": 0
    }

    resposta = fazer_get(
        sessao,
        SEARCH_URL,
        parametros
    )

    if resposta is None:
        return []

    if resposta.status_code != 200:

        print(
            f"❌ Busca '{termo}' retornou "
            f"HTTP {resposta.status_code}"
        )

        try:
            erro = resposta.json()

            print(
                f"   Erro: "
                f"{erro.get('error')}"
            )

            print(
                f"   Mensagem: "
                f"{erro.get('message')}"
            )

        except ValueError:
            pass

        return []

    try:
        dados = resposta.json()

    except ValueError:

        print(
            f"❌ JSON inválido na busca: "
            f"{termo}"
        )

        return []

    resultados = dados.get(
        "results",
        []
    )

    print(
        f"🔎 '{termo}': "
        f"{len(resultados)} itens encontrados."
    )

    return resultados


# ============================================================
# CONSULTAR PREÇO PROMOCIONAL
# ============================================================

def consultar_preco_item(
    sessao,
    item_id
):
    """
    Consulta o endpoint atual de preço.

    Retorno esperado:

    {
        "amount": 799.90,
        "regular_amount": 999.90
    }
    """

    url = (
        f"{API_BASE_URL}/items/"
        f"{item_id}/sale_price"
    )

    parametros = {
        "context": "channel_marketplace"
    }

    resposta = fazer_get(
        sessao,
        url,
        parametros
    )

    if resposta is None:
        return None

    if resposta.status_code != 200:

        print(
            f"⚠️ Preço indisponível para "
            f"{item_id}: HTTP "
            f"{resposta.status_code}"
        )

        return None

    try:
        dados = resposta.json()

    except ValueError:

        print(
            f"⚠️ Preço inválido para "
            f"{item_id}."
        )

        return None

    preco_atual = converter_numero(
        dados.get("amount")
    )

    preco_anterior = converter_numero(
        dados.get("regular_amount")
    )

    if preco_atual is None:
        return None

    # Sem regular_amount não temos como
    # comprovar que existe desconto real.
    if preco_anterior is None:
        return None

    if preco_anterior <= 0:
        return None

    if preco_atual <= 0:
        return None

    if preco_atual >= preco_anterior:
        return None

    desconto = (
        (
            preco_anterior
            - preco_atual
        )
        / preco_anterior
    ) * 100

    return {
        "preco_anterior": preco_anterior,
        "preco_atual": preco_atual,
        "desconto": desconto
    }


# ============================================================
# NORMALIZAR PRODUTO
# ============================================================

def normalizar_produto(
    item,
    dados_preco
):
    """
    Converte o produto do Mercado Livre
    para o padrão do deal_processor.py.
    """

    item_id = item.get("id")
    nome = item.get("title")
    url = item.get("permalink")
    imagem = item.get("thumbnail")
    condicao = item.get("condition")

    if not item_id:
        return None

    if not nome:
        return None

    if not url:
        return None

    # Evita itens usados no bot de promoções
    if condicao and condicao != "new":
        return None

    imagem = normalizar_imagem(
        imagem
    )

    return {
        "nome": nome.strip(),
        "loja": "Mercado Livre",
        "preco_anterior": (
            dados_preco["preco_anterior"]
        ),
        "preco_atual": (
            dados_preco["preco_atual"]
        ),
        "url": url,
        "imagem": imagem,

        # Metadados opcionais.
        # O deal_processor ignora estes campos,
        # mas podem ajudar nos diagnósticos.
        "item_id": item_id,
        "origem": "mercado_livre"
    }


# ============================================================
# BUSCAR OFERTAS
# ============================================================

def buscar_ofertas_mercado_livre(
    limite_por_busca=LIMITE_POR_BUSCA
):
    """
    Função principal do coletor.

    Retorna:

    [
        {
            "nome": "...",
            "loja": "Mercado Livre",
            "preco_anterior": 999.90,
            "preco_atual": 799.90,
            "url": "...",
            "imagem": "..."
        }
    ]
    """

    print(
        "\n🟡 INICIANDO COLETOR "
        "DO MERCADO LIVRE"
    )

    print("=" * 70)

    access_token = obter_access_token()

    if not access_token:

        print(
            "❌ Mercado Livre sem "
            "Access Token válido."
        )

        return []

    sessao = criar_sessao(
        access_token
    )

    ofertas = []

    itens_processados = set()

    for termo in TERMOS_BUSCA:

        itens = buscar_itens_por_termo(
            sessao,
            termo,
            limite_por_busca
        )

        for item in itens:

            item_id = item.get("id")

            if not item_id:
                continue

            # Evita o mesmo anúncio aparecendo
            # em várias buscas.
            if item_id in itens_processados:
                continue

            itens_processados.add(
                item_id
            )

            # Apenas produtos novos
            if item.get("condition") != "new":
                continue

            dados_preco = consultar_preco_item(
                sessao,
                item_id
            )

            if not dados_preco:
                continue

            produto = normalizar_produto(
                item,
                dados_preco
            )

            if not produto:
                continue

            ofertas.append(
                produto
            )

            print(
                f"✅ Oferta encontrada: "
                f"{produto['nome']}"
            )

            print(
                f"   R$ "
                f"{produto['preco_anterior']:.2f}"
                f" -> R$ "
                f"{produto['preco_atual']:.2f}"
            )

            print(
                f"   Desconto: "
                f"{dados_preco['desconto']:.2f}%"
            )

            time.sleep(
                INTERVALO_REQUISICOES
            )

        time.sleep(
            INTERVALO_REQUISICOES
        )

    print("\n" + "=" * 70)

    print(
        f"🟡 Mercado Livre: "
        f"{len(ofertas)} ofertas válidas."
    )

    print(
        f"📦 Itens únicos analisados: "
        f"{len(itens_processados)}"
    )

    print("=" * 70)

    return ofertas


# ============================================================
# ALIAS PARA O SCHEDULER
# ============================================================

def coletar_ofertas():
    """
    Permite que o scheduler utilize
    o mesmo padrão dos outros collectors.
    """

    return buscar_ofertas_mercado_livre()


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":

    ofertas = buscar_ofertas_mercado_livre(
        limite_por_busca=5
    )

    print(
        "\n🧪 RESULTADO DO TESTE ISOLADO"
    )

    print("=" * 70)

    if not ofertas:

        print(
            "\n⚠️ Nenhuma oferta promocional "
            "foi encontrada."
        )

        print(
            "Isso pode significar que os itens "
            "retornados não possuem "
            "regular_amount maior que amount."
        )

    for indice, produto in enumerate(
        ofertas[:20],
        start=1
    ):

        desconto = (
            (
                produto["preco_anterior"]
                - produto["preco_atual"]
            )
            / produto["preco_anterior"]
        ) * 100

        print(
            f"\n📦 Oferta #{indice}"
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

        print(
            f"Desconto: "
            f"{desconto:.2f}%"
        )

        print(
            f"Item ID: "
            f"{produto['item_id']}"
        )

        print(
            f"URL: {produto['url']}"
        )

        print(
            f"Imagem: {produto['imagem']}"
        )

        print("-" * 70)