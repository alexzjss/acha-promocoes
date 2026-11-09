import asyncio
import sys
import threading
import time
from pathlib import Path

import requests


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# IMPORTS INTERNOS
# ============================================================

from collectors.common import (
    calcular_desconto,
    validar_precos,
)

from services.mercado_livre_auth import (
    obter_access_token,
    renovar_access_token,
)

from services.filtro_tecnologia import (
    filtrar_produtos_tecnologia,
    validar_produto_tecnologia,
)

from services.afiliados_db import (
    inicializar_banco,
    adicionar_url,
    buscar_url_afiliada,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

SITE_ID = "MLB"

API_BASE_URL = "https://api.mercadolibre.com"

# Endpoint que já testamos e retornou HTTP 200.
SEARCH_URL = f"{API_BASE_URL}/products/search"

TIMEOUT = 30

LIMITE_POR_BUSCA = 30

# Número máximo de requisições simultâneas.
CONCORRENCIA = 4

# Tentativas para 429 e erros temporários da API.
TENTATIVAS = 3


TERMOS_BUSCA = [
    "placa de video",
    "processador ryzen",
    "processador intel core",
    "placa mae",
    "memoria ram ddr4",
    "memoria ram ddr5",
    "ssd nvme",
    "ssd sata",
    "hd externo",
    "fonte gamer",
    "water cooler",
    "cooler processador",
    "kit fan gabinete",
    "gabinete gamer",
    "monitor gamer",
    "suporte monitor",
    "mouse gamer",
    "teclado gamer",
    "teclado mecanico",
    "headset gamer",
    "webcam",
    "microfone gamer",
    "cadeira gamer",
    "mousepad gamer",
    "controle gamer",
    "notebook gamer",
    "action figure",
    "funko pop",
]


# ============================================================
# EXCEÇÕES
# ============================================================

class AcessoNegado(Exception):
    """
    Indica que a API bloqueou um endpoint crítico
    com HTTP 403.
    """


# ============================================================
# CLIENTE HTTP
# ============================================================

class ClienteML:
    """
    Cliente HTTP compartilhado entre as threads.

    Comportamento:

    - HTTP 200: retorna o JSON.
    - HTTP 401: renova o token uma vez.
    - HTTP 403: levanta AcessoNegado.
    - HTTP 404: retorna None.
    - HTTP 429/5xx: aplica retry com backoff.
    """

    def __init__(self, access_token):
        self.access_token = access_token
        self._lock = threading.Lock()

    def _headers(self):
        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            ),
            "Accept": "application/json",
            "User-Agent": (
                "Acha-Promocoes/1.0 "
                "(Discord promotion bot)"
            ),
        }

    def _renovar(self, token_usado):
        """
        Renova o token de forma segura quando várias
        threads recebem HTTP 401 ao mesmo tempo.
        """

        with self._lock:
            # Outra thread já renovou o token.
            if self.access_token != token_usado:
                return True

            novo_token = renovar_access_token()

            if not novo_token:
                return False

            self.access_token = novo_token

            return True

    def get(
        self,
        url,
        parametros=None,
        ignorar_403=False,
    ):
        """
        Executa uma requisição GET autenticada.

        ignorar_403=True pode ser usado em endpoints
        auxiliares para descartar somente aquele produto,
        sem interromper toda a coleta.
        """

        renovou = False

        for tentativa in range(TENTATIVAS):
            token_usado = self.access_token

            try:
                resposta = requests.get(
                    url,
                    params=parametros,
                    headers=self._headers(),
                    timeout=TIMEOUT,
                )

            except requests.RequestException as erro:
                print(
                    "❌ Erro de rede no Mercado Livre: "
                    f"{erro}"
                )

                resposta = None

            if resposta is not None:
                status = resposta.status_code

                if status == 200:
                    try:
                        return resposta.json()

                    except ValueError:
                        print(
                            f"❌ JSON inválido em {url}"
                        )

                        return None

                if status == 401 and not renovou:
                    renovou = True

                    print(
                        "⚠️ HTTP 401 no Mercado Livre. "
                        "Renovando token..."
                    )

                    if self._renovar(token_usado):
                        continue

                    return None

                if status == 403:
                    if ignorar_403:
                        print(
                            "⚠️ HTTP 403 ignorado em "
                            f"{url}"
                        )

                        return None

                    raise AcessoNegado(url)

                if status == 404:
                    return None

                if status not in (
                    429,
                    500,
                    502,
                    503,
                    504,
                ):
                    print(
                        f"⚠️ HTTP {status} em {url}"
                    )

                    try:
                        dados_erro = resposta.json()

                        print(
                            "   Erro: "
                            f"{dados_erro.get('error')}"
                        )

                        print(
                            "   Mensagem: "
                            f"{dados_erro.get('message')}"
                        )

                    except ValueError:
                        pass

                    return None

            if tentativa < TENTATIVAS - 1:
                espera = 2 ** tentativa

                time.sleep(espera)

        return None


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def converter_numero(valor):
    """
    Converte um valor para float.
    """

    if valor is None:
        return None

    try:
        return float(valor)

    except (TypeError, ValueError):
        return None


def normalizar_imagem(url):
    """
    Garante que a URL da imagem utilize HTTPS.
    """

    if not url:
        return None

    url = str(url).strip()

    if url.startswith("http://"):
        return url.replace(
            "http://",
            "https://",
            1,
        )

    return url


def extrair_imagem(produto_catalogo, item_detalhes):
    """
    Prioriza a imagem do anúncio individual.

    Caso não exista, utiliza a primeira imagem
    do produto de catálogo.
    """

    thumbnail = item_detalhes.get(
        "secure_thumbnail"
    )

    if not thumbnail:
        thumbnail = item_detalhes.get(
            "thumbnail"
        )

    if thumbnail:
        return normalizar_imagem(
            thumbnail
        )

    imagens_item = item_detalhes.get(
        "pictures"
    ) or []

    if imagens_item:
        primeira = imagens_item[0]

        if isinstance(primeira, dict):
            imagem = (
                primeira.get("secure_url")
                or primeira.get("url")
            )

            if imagem:
                return normalizar_imagem(
                    imagem
                )

    imagens_catalogo = produto_catalogo.get(
        "pictures"
    ) or []

    if imagens_catalogo:
        primeira = imagens_catalogo[0]

        if isinstance(primeira, dict):
            imagem = primeira.get("url")

            if imagem:
                return normalizar_imagem(
                    imagem
                )

    return None


# ============================================================
# BUSCAR PRODUTOS DE CATÁLOGO
# ============================================================

def buscar_produtos_por_termo(
    cliente,
    termo,
    limite,
):
    """
    Busca produtos no catálogo do Mercado Livre.

    Usa /products/search porque o endpoint antigo
    /sites/MLB/search?q=... retorna HTTP 403.

    A primeira barreira do filtro é aplicada aqui.
    """

    dados = cliente.get(
        SEARCH_URL,
        {
            "status": "active",
            "site_id": SITE_ID,
            "q": termo,
            "limit": limite,
            "offset": 0,
        },
    )

    if not dados:
        print(
            f"⚠️ Nenhum resultado para '{termo}'."
        )

        return []

    resultados = dados.get(
        "results",
        [],
    )

    if not isinstance(resultados, list):
        return []

    print(
        f"🔎 '{termo}': "
        f"{len(resultados)} produtos encontrados."
    )

    quantidade_original = len(resultados)

    resultados_filtrados = (
        filtrar_produtos_tecnologia(
            resultados,
            exibir_ignorados=False,
        )
    )

    print(
        f"🧹 '{termo}': "
        f"{len(resultados_filtrados)} de "
        f"{quantidade_original} aprovados "
        "pelo filtro de tecnologia."
    )

    return resultados_filtrados


# ============================================================
# CONSULTAR OFERTAS DO PRODUTO
# ============================================================

def melhor_oferta_do_produto(
    cliente,
    produto_id,
):
    """
    Consulta os anúncios associados ao produto
    de catálogo.

    Retorna o anúncio novo com o maior desconto
    real encontrado.
    """

    url = (
        f"{API_BASE_URL}/products/"
        f"{produto_id}/items"
    )

    dados = cliente.get(
        url,
        ignorar_403=True,
    )

    if not dados:
        return None

    resultados = dados.get(
        "results",
        [],
    )

    if not isinstance(resultados, list):
        return None

    melhor_oferta = None
    melhor_desconto = 0

    for oferta in resultados:
        if not isinstance(oferta, dict):
            continue

        condicao = oferta.get("condition")

        if condicao and condicao != "new":
            continue

        preco_atual = converter_numero(
            oferta.get("price")
        )

        preco_anterior = converter_numero(
            oferta.get("original_price")
        )

        item_id = (
            oferta.get("item_id")
            or oferta.get("id")
        )

        if not item_id:
            continue

        if preco_atual is None:
            continue

        if preco_anterior is None:
            continue

        if preco_atual <= 0:
            continue

        if preco_anterior <= 0:
            continue

        if preco_atual >= preco_anterior:
            continue

        desconto = calcular_desconto(
            preco_anterior,
            preco_atual,
        )

        if desconto <= 0:
            continue

        if desconto > melhor_desconto:
            melhor_desconto = desconto

            melhor_oferta = {
                "item_id": item_id,
                "preco_anterior": preco_anterior,
                "preco_atual": preco_atual,
                "desconto": desconto,
            }

    return melhor_oferta


# ============================================================
# CONSULTAR DETALHES DO ANÚNCIO
# ============================================================

def consultar_item(
    cliente,
    item_id,
):
    """
    Consulta o anúncio individual para recuperar
    título, permalink, imagem e condição.
    """

    url = (
        f"{API_BASE_URL}/items/"
        f"{item_id}"
    )

    return cliente.get(
        url,
        ignorar_403=True,
    )


# ============================================================
# PREPARAR LINK AFILIADO
# ============================================================

def preparar_link_afiliado(
    item_id,
    url_original,
):
    """
    Registra a URL original no banco.

    Se o produto já tiver link convertido,
    retorna a URL afiliada.

    Caso contrário, retorna a URL original.
    """

    try:
        adicionar_url(
            loja="Mercado Livre",
            item_id=item_id,
            url_original=url_original,
        )

    except Exception as erro:
        print(
            "⚠️ Não foi possível adicionar "
            f"{item_id} à fila de afiliados: "
            f"{erro}"
        )

    try:
        url_afiliado = buscar_url_afiliada(
            loja="Mercado Livre",
            item_id=item_id,
        )

    except Exception as erro:
        print(
            "⚠️ Não foi possível consultar "
            f"o afiliado de {item_id}: {erro}"
        )

        url_afiliado = None

    if url_afiliado:
        return {
            "url_publicacao": url_afiliado,
            "url_afiliado": url_afiliado,
            "status_afiliado": "convertido",
        }

    return {
        "url_publicacao": url_original,
        "url_afiliado": None,
        "status_afiliado": "pendente",
    }


# ============================================================
# NORMALIZAR PRODUTO
# ============================================================

def normalizar_produto(
    produto_catalogo,
    item_detalhes,
    oferta,
    categoria_tecnologia,
):
    """
    Converte o resultado para o padrão esperado
    pelo deal_processor.py.
    """

    item_id = oferta.get("item_id")

    nome = (
        item_detalhes.get("title")
        or produto_catalogo.get("name")
    )

    url_original = item_detalhes.get(
        "permalink"
    )

    condicao = item_detalhes.get(
        "condition"
    )

    if not item_id:
        return None

    if not nome:
        return None

    if not url_original:
        return None

    if condicao and condicao != "new":
        return None

    nome = str(nome).strip()
    url_original = str(
        url_original
    ).strip()

    if not nome or not url_original:
        return None

    imagem = extrair_imagem(
        produto_catalogo,
        item_detalhes,
    )

    dados_afiliado = preparar_link_afiliado(
        item_id=item_id,
        url_original=url_original,
    )

    preco_anterior = oferta[
        "preco_anterior"
    ]

    preco_atual = oferta[
        "preco_atual"
    ]

    desconto = oferta[
        "desconto"
    ]

    return {
        "nome": nome,
        "loja": "Mercado Livre",

        "preco_anterior": round(
            preco_anterior,
            2,
        ),

        "preco_atual": round(
            preco_atual,
            2,
        ),

        "desconto": round(
            desconto,
            2,
        ),

        # URL consumida pelo deal_processor.
        "url": dados_afiliado[
            "url_publicacao"
        ],

        "url_original": url_original,

        "url_afiliado": dados_afiliado[
            "url_afiliado"
        ],

        "status_afiliado": dados_afiliado[
            "status_afiliado"
        ],

        "imagem": imagem,

        "item_id": item_id,

        "catalog_product_id": (
            produto_catalogo.get("id")
        ),

        "domain_id": (
            produto_catalogo.get(
                "domain_id"
            )
        ),

        "categoria_tecnologia": (
            categoria_tecnologia
        ),

        "origem": "mercado_livre",

        "condicao": (
            condicao
            or "new"
        ),
    }


# ============================================================
# PROCESSAR PRODUTO DO CATÁLOGO
# ============================================================

def processar_produto_catalogo(
    cliente,
    resumo,
):
    """
    Processa um produto de catálogo.

    Etapas:

    1. Segunda validação de tecnologia.
    2. Consulta anúncios associados.
    3. Escolhe o anúncio com melhor desconto.
    4. Consulta o Item ID real.
    5. Valida preços.
    6. Normaliza para o deal_processor.
    """

    produto_id = resumo.get("id")

    if not produto_id:
        return None

    # ========================================================
    # SEGUNDA BARREIRA DE TECNOLOGIA
    # ========================================================

    resultado_filtro = (
        validar_produto_tecnologia(
            resumo
        )
    )

    if not resultado_filtro["aprovado"]:
        return None

    categoria_tecnologia = (
        resultado_filtro["categoria"]
    )

    # ========================================================
    # MELHOR ANÚNCIO ASSOCIADO
    # ========================================================

    oferta = melhor_oferta_do_produto(
        cliente,
        produto_id,
    )

    if not oferta:
        return None

    item_id = oferta.get("item_id")

    if not item_id:
        return None

    # ========================================================
    # DETALHES DO ANÚNCIO REAL
    # ========================================================

    item_detalhes = consultar_item(
        cliente,
        item_id,
    )

    if not item_detalhes:
        return None

    nome_validacao = (
        item_detalhes.get("title")
        or resumo.get("name")
    )

    preco_anterior = oferta[
        "preco_anterior"
    ]

    preco_atual = oferta[
        "preco_atual"
    ]

    if not validar_precos(
        nome_validacao,
        preco_anterior,
        preco_atual,
    ):
        return None

    produto_normalizado = (
        normalizar_produto(
            produto_catalogo=resumo,
            item_detalhes=item_detalhes,
            oferta=oferta,
            categoria_tecnologia=(
                categoria_tecnologia
            ),
        )
    )

    if not produto_normalizado:
        return None

    # ========================================================
    # TERCEIRA BARREIRA ANTES DO PIPELINE
    # ========================================================

    validacao_final = (
        validar_produto_tecnologia(
            produto_normalizado
        )
    )

    if not validacao_final["aprovado"]:
        print(
            "⛔ Produto bloqueado na "
            "validação final:"
        )

        print(
            f"   {produto_normalizado['nome']}"
        )

        print(
            "   Motivo: "
            f"{validacao_final['motivo']}"
        )

        return None

    produto_normalizado[
        "categoria_tecnologia"
    ] = validacao_final["categoria"]

    return produto_normalizado


# ============================================================
# COLETOR PRINCIPAL
# ============================================================

async def buscar_ofertas_mercado_livre(
    limite_por_busca=LIMITE_POR_BUSCA,
):
    """
    Retorna produtos no padrão esperado pelo
    deal_processor.py.

    O I/O bloqueante é executado em threads para
    não travar o loop do bot do Discord.
    """

    print("\n" + "=" * 70)
    print("🟡 COLETOR MERCADO LIVRE")
    print("=" * 70)

    # ========================================================
    # INICIALIZAR SQLITE
    # ========================================================

    try:
        await asyncio.to_thread(
            inicializar_banco
        )

    except Exception as erro:
        print(
            "❌ Erro inicializando banco "
            f"de afiliados: {erro}"
        )

        return []

    # ========================================================
    # AUTENTICAÇÃO
    # ========================================================

    access_token = await asyncio.to_thread(
        obter_access_token
    )

    if not access_token:
        print(
            "❌ Mercado Livre sem "
            "Access Token válido."
        )

        return []

    cliente = ClienteML(
        access_token
    )

    semaforo = asyncio.Semaphore(
        CONCORRENCIA
    )

    async def limitado(
        funcao,
        *args,
    ):
        async with semaforo:
            return await asyncio.to_thread(
                funcao,
                *args,
            )

    ofertas = []

    catalogos_vistos = set()
    anuncios_vistos = set()

    try:
        # ====================================================
        # BUSCAR TERMOS
        # ====================================================

        buscas = await asyncio.gather(
            *(
                limitado(
                    buscar_produtos_por_termo,
                    cliente,
                    termo,
                    limite_por_busca,
                )
                for termo in TERMOS_BUSCA
            )
        )

        # ====================================================
        # REMOVER CATÁLOGOS DUPLICADOS
        # ====================================================

        produtos_unicos = []

        for produtos in buscas:
            for produto in produtos:
                produto_id = produto.get("id")

                if not produto_id:
                    continue

                if produto_id in catalogos_vistos:
                    continue

                catalogos_vistos.add(
                    produto_id
                )

                produtos_unicos.append(
                    produto
                )

        print(
            f"\n📚 Produtos únicos de catálogo: "
            f"{len(produtos_unicos)}"
        )

        # ====================================================
        # PROCESSAR PRODUTOS
        # ====================================================

        resultados = await asyncio.gather(
            *(
                limitado(
                    processar_produto_catalogo,
                    cliente,
                    produto,
                )
                for produto in produtos_unicos
            )
        )

    except AcessoNegado as erro:
        print(
            "🚫 Mercado Livre negou acesso "
            f"(HTTP 403) em {erro}."
        )

        print(
            "O endpoint bloqueado é diferente "
            "do /products/search que já foi "
            "validado com HTTP 200."
        )

        return []

    # ========================================================
    # RESULTADOS FINAIS
    # ========================================================

    links_convertidos = 0
    links_pendentes = 0

    for produto in resultados:
        if not produto:
            continue

        item_id = produto.get("item_id")

        if not item_id:
            continue

        # Evita publicar o mesmo anúncio duas vezes
        # dentro da mesma execução.
        if item_id in anuncios_vistos:
            continue

        anuncios_vistos.add(
            item_id
        )

        ofertas.append(
            produto
        )

        if (
            produto.get("status_afiliado")
            == "convertido"
        ):
            links_convertidos += 1

        else:
            links_pendentes += 1

        desconto = calcular_desconto(
            produto["preco_anterior"],
            produto["preco_atual"],
        )

        print(
            f"\n✅ {produto['nome'][:70]}"
        )

        print(
            "   Categoria: "
            f"{produto['categoria_tecnologia']}"
        )

        print(
            f"   R$ "
            f"{produto['preco_anterior']:.2f}"
            f" -> R$ "
            f"{produto['preco_atual']:.2f}"
            f" ({desconto:.2f}% OFF)"
        )

        print(
            "   Afiliado: "
            f"{produto['status_afiliado']}"
        )

    print("\n" + "-" * 70)

    print(
        f"🟡 Mercado Livre: "
        f"{len(ofertas)} ofertas válidas."
    )

    print(
        f"📚 Catálogos únicos analisados: "
        f"{len(catalogos_vistos)}"
    )

    print(
        f"📦 Anúncios únicos aprovados: "
        f"{len(anuncios_vistos)}"
    )

    print(
        f"✅ Links afiliados convertidos: "
        f"{links_convertidos}"
    )

    print(
        f"🔗 Links afiliados pendentes: "
        f"{links_pendentes}"
    )

    print("-" * 70)

    return ofertas


# ============================================================
# INTERFACE DO SCHEDULER
# ============================================================

async def coletar_ofertas(
    limite=None,
):
    """
    Interface padrão utilizada pelo scheduler.
    """

    ofertas = (
        await buscar_ofertas_mercado_livre()
    )

    if limite:
        return ofertas[:limite]

    return ofertas


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":
    resultado = asyncio.run(
        buscar_ofertas_mercado_livre(
            limite_por_busca=5
        )
    )

    print(
        f"\n🧪 {len(resultado)} ofertas "
        "no teste isolado."
    )

    for indice, produto in enumerate(
        resultado[:10],
        start=1,
    ):
        print("\n" + "=" * 70)

        print(
            f"OFERTA #{indice}"
        )

        print(
            f"Nome: {produto['nome']}"
        )

        print(
            "Categoria: "
            f"{produto['categoria_tecnologia']}"
        )

        print(
            f"Item ID: {produto['item_id']}"
        )

        print(
            "Catalog Product ID: "
            f"{produto['catalog_product_id']}"
        )

        print(
            f"Domain ID: {produto['domain_id']}"
        )

        print(
            "Preço anterior: "
            f"R$ {produto['preco_anterior']:.2f}"
        )

        print(
            "Preço atual: "
            f"R$ {produto['preco_atual']:.2f}"
        )

        print(
            "URL original: "
            f"{produto['url_original']}"
        )

        print(
            "URL afiliada: "
            f"{produto['url_afiliado']}"
        )

        print(
            "URL publicada: "
            f"{produto['url']}"
        )

        print(
            "Status afiliado: "
            f"{produto['status_afiliado']}"
        )