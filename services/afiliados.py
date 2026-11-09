"""
Camada de afiliados usada pelo pipeline para TODAS as lojas.

Fluxo:
  1. aplicar_afiliado(produto) registra o produto na fila (afiliados_db),
     converte na hora quando a loja tem regra por URL (Amazon, redes de
     afiliados) e devolve o produto com a URL a ser publicada.
  2. O Mercado Livre não tem regra por URL: o link oficial é gerado pelo
     portal de Afiliados (services/afiliados_conversor.py), que processa
     a fila em segundo plano. Enquanto pendente, publica-se a URL original.

Configuração (.env):
  AMAZON_ASSOCIATE_TAG=seu-id-20
  AFILIADO_TEMPLATE_KABUM=https://...{url_codificada}...
  AFILIADO_TEMPLATE_TERABYTE=...
  AFILIADO_TEMPLATE_PICHAU=...
  AFILIADO_TEMPLATE_MAGALU=...
Placeholders do template: {url} e {url_codificada}.
"""

import hashlib
import os
import re
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

from services.afiliados_db import (
    adicionar_url,
    buscar_url_afiliada,
    inicializar_banco,
    marcar_convertido,
)


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def chave_loja(loja):
    """'KaBuM!' -> 'KABUM'; 'Mercado Livre' -> 'MERCADOLIVRE'."""

    return re.sub(r"[^A-Z0-9]", "", str(loja).upper())


def item_id_estavel(loja, url):
    """Identificador estável do produto (ASIN, id da loja ou hash da URL)."""

    for padrao in (r"/dp/([A-Z0-9]{10})", r"/produto/(\d+)"):
        achado = re.search(padrao, url)

        if achado:
            return achado.group(1)

    return hashlib.sha1(url.split("?")[0].encode()).hexdigest()[:16]


def tem_regra(loja):
    """True se a loja converte por URL (sem portal)."""

    chave = chave_loja(loja)

    if chave == "AMAZON":
        return bool(os.getenv("AMAZON_ASSOCIATE_TAG"))

    return bool(os.getenv(f"AFILIADO_TEMPLATE_{chave}"))


def converter_por_regra(loja, url):
    """Gera o link afiliado por regra de URL ou None se não houver regra."""

    chave = chave_loja(loja)

    if chave == "AMAZON":
        tag = os.getenv("AMAZON_ASSOCIATE_TAG")

        if not tag:
            return None

        partes = urlparse(url)
        consulta = [
            (k, v) for k, v in parse_qsl(partes.query) if k != "tag"
        ]
        consulta.append(("tag", tag))

        return urlunparse(partes._replace(query=urlencode(consulta)))

    modelo = os.getenv(f"AFILIADO_TEMPLATE_{chave}")

    if not modelo:
        return None

    return modelo.replace("{url_codificada}", quote(url, safe="")).replace(
        "{url}", url
    )


def aplicar_afiliado(produto):
    """
    Devolve uma cópia do produto com:
      url             -> URL a publicar (afiliada quando disponível)
      url_original    -> URL sem afiliado (chave de histórico)
      url_afiliado    -> link afiliado ou None
      status_afiliado -> 'convertido' | 'pendente' | 'sem_afiliado'
    """

    produto = dict(produto)

    loja = produto["loja"]
    url_original = produto.get("url_original") or produto["url"]
    item_id = produto.get("item_id") or item_id_estavel(loja, url_original)

    produto["url_original"] = url_original

    url_afiliado = None

    try:
        inicializar_banco()

        regra = tem_regra(loja)
        ml = chave_loja(loja) == "MERCADOLIVRE"

        if not regra and not ml:
            produto.update(
                url=url_original,
                url_afiliado=None,
                status_afiliado="sem_afiliado",
            )
            return produto

        adicionar_url(loja, item_id, url_original)

        url_afiliado = buscar_url_afiliada(loja, item_id)

        if not url_afiliado and regra:
            url_afiliado = converter_por_regra(loja, url_original)

            if url_afiliado:
                marcar_convertido(loja, item_id, url_afiliado)

    except Exception as erro:
        print(f"⚠️ Afiliados indisponíveis para {loja}: {erro}")
        url_afiliado = None

    if url_afiliado:
        produto.update(
            url=url_afiliado,
            url_afiliado=url_afiliado,
            status_afiliado="convertido",
        )

    else:
        produto.update(
            url=url_original,
            url_afiliado=None,
            status_afiliado="pendente",
        )

    return produto
