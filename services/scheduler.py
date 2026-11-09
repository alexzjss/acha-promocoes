import asyncio
import importlib
import os
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collectors import COLETORES
from services.afiliados_conversor import converter_pendentes
from services.deal_processor import processar_produto


scheduler = AsyncIOScheduler()

LIMITE_POR_LOJA = 80


def carregar_coletor(caminho):
    modulo, funcao = caminho.split(":")

    return getattr(importlib.import_module(modulo), funcao)


async def coletar_loja(nome, caminho):
    """Executa um coletor isolado: falha de uma loja não afeta as outras."""

    try:
        coletor = carregar_coletor(caminho)

        produtos = await coletor(limite=LIMITE_POR_LOJA)

    except Exception as erro:
        print(f"❌ Erro durante coleta de {nome}: {erro}")
        return []

    if not produtos:
        print(f"⚠️ Nenhuma oferta válida encontrada em {nome}.")
        return []

    return produtos


async def verificar_ofertas(bot):
    print("\n" + "=" * 60)
    print("🔎 INICIANDO VERIFICAÇÃO AUTOMÁTICA DE OFERTAS")
    print("=" * 60)

    contadores = {
        "coletadas": 0,
        "publicada": 0,
        "duplicada": 0,
        "rejeitada": 0,
        "descartada": 0,
        "erro": 0,
        "afiliados": 0,
    }

    for nome, caminho in COLETORES:
        produtos = await coletar_loja(nome, caminho)

        contadores["coletadas"] += len(produtos)

        # Converte links de afiliado pendentes antes de publicar
        # (o processador relê a fila e usa o link convertido).
        if produtos:
            try:
                conversao = await converter_pendentes(limite=20)

                contadores["afiliados"] += conversao["convertidos"]

            except Exception as erro:
                print(f"⚠️ Erro convertendo links de afiliado: {erro}")

        for produto in produtos:
            try:
                resultado = await processar_produto(bot, produto)

                status = resultado.get("status", "erro")

            except Exception as erro:
                print(
                    f"❌ Erro processando "
                    f"{produto.get('nome', 'Produto desconhecido')}: {erro}"
                )
                status = "erro"

            print(f"📋 {produto.get('nome')} -> {status}")

            if status in ("publicada", "duplicada", "rejeitada"):
                contadores[status] += 1

            elif status in (
                "preco_invalido",
                "desconto_insuficiente",
                "preco_suspeito",
                "fora_do_nicho",
            ):
                contadores["descartada"] += 1

            else:
                contadores["erro"] += 1

            # Cede o loop para o Discord manter o heartbeat.
            await asyncio.sleep(0)

    print("\n" + "-" * 60)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("-" * 60)
    print(f"📦 Coletadas: {contadores['coletadas']}")
    print(f"🔥 Publicadas: {contadores['publicada']}")
    print(f"⏭️ Duplicadas: {contadores['duplicada']}")
    print(f"❌ Rejeitadas (score): {contadores['rejeitada']}")
    print(f"🚫 Descartadas (preço): {contadores['descartada']}")
    print(f"🔗 Links de afiliado convertidos: {contadores['afiliados']}")
    print(f"⚠️ Erros: {contadores['erro']}")
    print("-" * 60)
    print("✅ VERIFICAÇÃO FINALIZADA")
    print("=" * 60 + "\n")


def iniciar_scheduler(bot):
    if scheduler.running:
        print("⚠️ Scheduler já está executando.")
        return

    # Lido aqui (e não no import) para respeitar o .env já carregado.
    INTERVALO_MINUTOS = int(os.getenv("SCHEDULER_INTERVALO_MIN", "15"))

    scheduler.add_job(
        verificar_ofertas,
        trigger="interval",
        minutes=INTERVALO_MINUTOS,
        # Primeira coleta logo ao iniciar (senão o banco/ranking
        # ficaria vazio até o primeiro intervalo).
        next_run_time=datetime.now(),
        args=[bot],
        id="verificar_ofertas",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    lojas = ", ".join(nome for nome, _ in COLETORES)

    print("⏰ Scheduler iniciado.")
    print(f"🛒 Lojas: {lojas}")
    print(f"🕒 Verificação a cada {INTERVALO_MINUTOS} minuto(s).")
