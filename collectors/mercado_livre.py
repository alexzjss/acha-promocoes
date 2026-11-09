import asyncio
import sys
import threading
import time
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from collectors.common import calcular_desconto, validar_precos
from services.mercado_livre_auth import (
    obter_access_token,
    renovar_access_token,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

SITE_ID = "MLB"
API_BASE_URL = "https://api.mercadolibre.com"
SEARCH_URL = f"{API_BASE_URL}/sites/{SITE_ID}/search"

TIMEOUT = 30
LIMITE_POR_BUSCA = 30

# Requisições simultâneas à API (respeita o rate limit do ML).
CONCORRENCIA = 4
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


class AcessoNegado(Exception):
    """A API recusou o acesso (HTTP 403): abortar a coleta."""


# ============================================================
# CLIENTE HTTP (síncrono, executado em threads)
# ============================================================

class ClienteML:
    """
    Faz GETs autenticados. Em HTTP 401 renova o token uma única vez
    (mesmo com várias threads batendo ao mesmo tempo) e repete.
    Em 429/5xx repete com backoff exponencial.
    """

    def __init__(self, access_token):
        self.access_token = access_token
        self._lock = threading.Lock()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "Acha-Promocoes/1.0 (Discord promotion bot)",
        }

    def _renovar(self, token_usado):
        with self._lock:
            # Outra thread já renovou enquanto esperávamos o lock.
            if self.access_token != token_usado:
                return True

            novo = renovar_access_token()

            if not novo:
                return False

            self.access_token = novo
            return True

    def get(self, url, parametros=None):
        """
        Retorna o JSON da resposta ou None em caso de falha.
        Levanta AcessoNegado em HTTP 403.
        """

        renovou = False

        for tentativa in range(TENTATIVAS):
            token = self.access_token

            try:
                resposta = requests.get(
                    url,
                    params=parametros,
                    headers=self._headers(),
                    timeout=TIMEOUT,
                )

            except requests.RequestException as erro:
                print(f"❌ Erro de rede no Mercado Livre: {erro}")
                resposta = None

            if resposta is not None:
                status = resposta.status_code

                if status == 200:
                    try:
                        return resposta.json()

                    except ValueError:
                        print(f"❌ JSON inválido em {url}")
                        return None

                if status == 401 and not renovou:
                    renovou = True
                    print("⚠️ HTTP 401 no Mercado Livre. Renovando token...")

                    if self._renovar(token):
                        continue

                    return None

                if status == 403:
                    raise AcessoNegado(url)

                if status not in (429, 500, 502, 503, 504):
                    # 404 (item sem preço promocional) e afins não valem retry.
                    if status != 404:
                        print(f"⚠️ HTTP {status} em {url}")

                    return None

            if tentativa < TENTATIVAS - 1:
                time.sleep(2 ** tentativa)

        return None


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def converter_numero(valor):
    try:
        return float(valor) if valor is not None else None

    except (TypeError, ValueError):
        return None


def normalizar_imagem(url):
    if url and url.startswith("http://"):
        return "https://" + url[len("http://"):]

    return url or None


def melhor_oferta_do_produto(cliente, produto_id):
    """
    Consulta as ofertas do produto de catálogo e devolve a de maior
    desconto real (price < original_price, item novo), ou None.
    """

    dados = cliente.get(f"{API_BASE_URL}/products/{produto_id}/items")

    if not dados:
        return None

    melhor = None

    for oferta in dados.get("results", []):
        atual = converter_numero(oferta.get("price"))
        anterior = converter_numero(oferta.get("original_price"))

        if oferta.get("condition") != "new":
            continue

        if not atual or not anterior or anterior <= atual:
            continue

        if melhor is None or (anterior - atual) / anterior > (
            melhor[0] - melhor[1]
        ) / melhor[0]:
            melhor = (anterior, atual, oferta.get("item_id"))

    return melhor


def normalizar_produto(produto, preco_anterior, preco_atual, item_id):
    nome = produto.get("name")
    # O campo permalink do catálogo costuma vir vazio; a página
    # do produto de catálogo segue o padrão /p/{id}.
    url = produto.get("permalink") or (
        f"https://www.mercadolivre.com.br/p/{produto.get('id')}"
        if produto.get("id")
        else None
    )

    if not nome or not url:
        return None

    imagens = produto.get("pictures") or []
    imagem = (imagens[0].get("url") if imagens else None)

    return {
        "nome": nome.strip(),
        "loja": "Mercado Livre",
        "preco_anterior": round(preco_anterior, 2),
        "preco_atual": round(preco_atual, 2),
        "url": url,
        "imagem": normalizar_imagem(imagem),
        "item_id": item_id,
        "origem": "mercado_livre",
    }


def buscar_produtos_por_termo(cliente, termo, limite):
    """
    A busca pública /sites/MLB/search está bloqueada (403) para apps
    comuns; usamos a busca do catálogo, que continua liberada.
    """

    dados = cliente.get(
        f"{API_BASE_URL}/products/search",
        {
            "status": "active",
            "site_id": SITE_ID,
            "q": termo,
            "limit": limite,
        },
    )

    if not dados:
        return []

    resultados = dados.get("results", [])

    print(f"🔎 '{termo}': {len(resultados)} produtos de catálogo.")

    return resultados


def processar_produto_catalogo(cliente, resumo):
    """Roda em thread. Retorna o produto normalizado ou None."""

    produto_id = resumo.get("id")

    if not produto_id:
        return None

    oferta = melhor_oferta_do_produto(cliente, produto_id)

    if not oferta:
        return None

    anterior, atual, item_id = oferta

    if not validar_precos(resumo.get("name"), anterior, atual):
        return None

    detalhes = cliente.get(f"{API_BASE_URL}/products/{produto_id}")

    if not detalhes:
        return None

    return normalizar_produto(detalhes, anterior, atual, item_id)


# ============================================================
# COLETOR PRINCIPAL (assíncrono)
# ============================================================

async def buscar_ofertas_mercado_livre(
    limite_por_busca=LIMITE_POR_BUSCA,
):
    """
    Retorna uma lista de produtos no padrão do deal_processor.
    Todo o I/O bloqueante roda em threads, então o loop do
    Discord não trava durante a coleta.
    """

    print("\n" + "=" * 60)
    print("🟡 COLETOR MERCADO LIVRE")
    print("=" * 60)

    access_token = await asyncio.to_thread(obter_access_token)

    if not access_token:
        print("❌ Mercado Livre sem Access Token válido.")
        return []

    cliente = ClienteML(access_token)
    semaforo = asyncio.Semaphore(CONCORRENCIA)

    async def limitado(funcao, *args):
        async with semaforo:
            return await asyncio.to_thread(funcao, *args)

    ofertas = []
    ids_vistos = set()

    try:
        buscas = await asyncio.gather(
            *(
                limitado(buscar_produtos_por_termo, cliente, termo, limite_por_busca)
                for termo in TERMOS_BUSCA
            )
        )

        itens_unicos = []

        for itens in buscas:
            for item in itens:
                item_id = item.get("id")

                if item_id and item_id not in ids_vistos:
                    ids_vistos.add(item_id)
                    itens_unicos.append(item)

        resultados = await asyncio.gather(
            *(limitado(processar_produto_catalogo, cliente, item) for item in itens_unicos)
        )

    except AcessoNegado as erro:
        print(
            "🚫 Mercado Livre negou acesso (HTTP 403) em "
            f"{erro}. Verifique permissões do app e se a busca "
            "pública está liberada para suas credenciais."
        )
        return []

    for produto in resultados:
        if not produto:
            continue

        ofertas.append(produto)

        desconto = calcular_desconto(
            produto["preco_anterior"], produto["preco_atual"]
        )

        print(
            f"✅ {produto['nome'][:70]}\n"
            f"   R$ {produto['preco_anterior']:.2f} -> "
            f"R$ {produto['preco_atual']:.2f} ({desconto:.2f}% OFF)"
        )

    print("-" * 60)
    print(f"🟡 Mercado Livre: {len(ofertas)} ofertas válidas.")
    print(f"📦 Itens únicos analisados: {len(ids_vistos)}")
    print("-" * 60)

    return ofertas


async def coletar_ofertas(limite=None):
    """Interface padrão dos coletores usada pelo scheduler."""

    ofertas = await buscar_ofertas_mercado_livre()

    return ofertas[:limite] if limite else ofertas


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":
    resultado = asyncio.run(
        buscar_ofertas_mercado_livre(limite_por_busca=5)
    )

    print(f"\n🧪 {len(resultado)} ofertas no teste isolado.")
