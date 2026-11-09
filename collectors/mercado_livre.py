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
LIMITE_POR_BUSCA = 10

# Requisições simultâneas à API (respeita o rate limit do ML).
CONCORRENCIA = 4
TENTATIVAS = 3

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


def precos_do_resultado(item):
    """
    O resultado da busca já traz `price` e, em itens em promoção,
    `original_price`. Evita uma chamada extra por item.
    """

    atual = converter_numero(item.get("price"))
    anterior = converter_numero(item.get("original_price"))

    if atual and anterior and anterior > atual:
        return anterior, atual

    return None


def consultar_preco_item(cliente, item_id):
    """
    Fallback: consulta /items/{id}/sale_price.
    Retorna (preco_anterior, preco_atual) ou None.
    """

    dados = cliente.get(
        f"{API_BASE_URL}/items/{item_id}/sale_price",
        {"context": "channel_marketplace"},
    )

    if not dados:
        return None

    atual = converter_numero(dados.get("amount"))
    anterior = converter_numero(dados.get("regular_amount"))

    if not atual or not anterior:
        return None

    return anterior, atual


def normalizar_produto(item, preco_anterior, preco_atual):
    item_id = item.get("id")
    nome = item.get("title")
    url = item.get("permalink")

    if not item_id or not nome or not url:
        return None

    if item.get("condition") != "new":
        return None

    return {
        "nome": nome.strip(),
        "loja": "Mercado Livre",
        "preco_anterior": round(preco_anterior, 2),
        "preco_atual": round(preco_atual, 2),
        "url": url,
        "imagem": normalizar_imagem(item.get("thumbnail")),
        "item_id": item_id,
        "origem": "mercado_livre",
    }


def buscar_itens_por_termo(cliente, termo, limite):
    dados = cliente.get(
        SEARCH_URL,
        {"q": termo, "limit": limite, "offset": 0, "condition": "new"},
    )

    if not dados:
        return []

    resultados = dados.get("results", [])

    print(f"🔎 '{termo}': {len(resultados)} itens encontrados.")

    return resultados


def processar_item(cliente, item):
    """Roda em thread. Retorna o produto normalizado ou None."""

    item_id = item.get("id")

    if not item_id or item.get("condition") != "new":
        return None

    if item.get("available_quantity") == 0:
        return None

    precos = precos_do_resultado(item) or consultar_preco_item(
        cliente, item_id
    )

    if not precos:
        return None

    anterior, atual = precos

    if not validar_precos(item.get("title"), anterior, atual):
        return None

    return normalizar_produto(item, anterior, atual)


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
                limitado(buscar_itens_por_termo, cliente, termo, limite_por_busca)
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
            *(limitado(processar_item, cliente, item) for item in itens_unicos)
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
