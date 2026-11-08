from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collectors.kabum import buscar_ofertas_kabum
from services.deal_processor import processar_produto


scheduler = AsyncIOScheduler()


async def verificar_ofertas(bot):
    print("\n" + "=" * 60)
    print("🔎 INICIANDO VERIFICAÇÃO AUTOMÁTICA DE OFERTAS")
    print("=" * 60)

    # ==========================================
    # COLETAR OFERTAS DA KABUM
    # ==========================================

    try:
        produtos = await buscar_ofertas_kabum(
            limite=20
        )

    except Exception as erro:
        print(
            f"❌ Erro durante coleta da KaBuM!: {erro}"
        )
        return

    if not produtos:
        print(
            "⚠️ Nenhuma oferta válida encontrada na KaBuM!."
        )
        return

    print(
        f"📦 Produtos recebidos pelo scheduler: "
        f"{len(produtos)}"
    )

    # ==========================================
    # CONTADORES
    # ==========================================

    publicadas = 0
    duplicadas = 0
    rejeitadas = 0
    erros = 0

    # ==========================================
    # PROCESSAR CADA PRODUTO
    # ==========================================

    for produto in produtos:
        try:
            resultado = await processar_produto(
                bot,
                produto
            )

            status = resultado.get(
                "status",
                "erro"
            )

            print(
                f"📋 {produto['nome']} -> {status}"
            )

            if status == "publicada":
                publicadas += 1

            elif status == "duplicada":
                duplicadas += 1

            elif status == "rejeitada":
                rejeitadas += 1

            else:
                erros += 1

        except Exception as erro:
            erros += 1

            print(
                f"❌ Erro processando "
                f"{produto.get('nome', 'Produto desconhecido')}: "
                f"{erro}"
            )

    # ==========================================
    # RESUMO
    # ==========================================

    print("\n" + "-" * 60)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("-" * 60)

    print(
        f"📦 Coletadas: {len(produtos)}"
    )

    print(
        f"🔥 Publicadas: {publicadas}"
    )

    print(
        f"⏭️ Duplicadas: {duplicadas}"
    )

    print(
        f"❌ Rejeitadas: {rejeitadas}"
    )

    print(
        f"⚠️ Erros: {erros}"
    )

    print("-" * 60)
    print("✅ VERIFICAÇÃO FINALIZADA")
    print("=" * 60 + "\n")


def iniciar_scheduler(bot):
    if scheduler.running:
        print(
            "⚠️ Scheduler já está executando."
        )
        return

    scheduler.add_job(
        verificar_ofertas,
        trigger="interval",

        # Mantemos 60 segundos apenas durante os testes
        seconds=60,

        args=[bot],

        id="verificar_ofertas_kabum",

        replace_existing=True,

        max_instances=1,

        coalesce=True
    )

    scheduler.start()

    print("⏰ Scheduler iniciado.")

    print(
        "🟠 KaBuM! será verificada "
        "a cada 60 segundos."
    )