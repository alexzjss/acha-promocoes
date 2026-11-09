from services.category_classifier import eh_tecnologia, identificar_categoria
from services.channel_router import escolher_canal
from services.deal_score import analisar_oferta
from services.afiliados import aplicar_afiliado
from services.alertas import notificar_alertas
from services.discord_sender import enviar_oferta

from database import (
    oferta_ja_publicada,
    registrar_oferta_publicada,
    salvar_produto
)


DESCONTO_MINIMO = 5
DESCONTO_MAXIMO = 70


async def processar_produto(bot, produto):
    """
    Pipeline completo de processamento:

    Produto
        -> validação
        -> categoria
        -> Deal Score
        -> segurança de preço
        -> histórico
        -> anti-duplicação
        -> roteamento
        -> Discord
    """

    # ========================================================
    # 1. VALIDAR CAMPOS OBRIGATÓRIOS
    # ========================================================

    campos_obrigatorios = [
        "nome",
        "loja",
        "preco_anterior",
        "preco_atual",
        "url"
    ]

    for campo in campos_obrigatorios:
        if campo not in produto:
            print(
                f"❌ Produto inválido. "
                f"Campo ausente: {campo}"
            )

            return {
                "status": "erro",
                "motivo": f"Campo ausente: {campo}"
            }

    # ========================================================
    # 1.1 LINK DE AFILIADO
    # ========================================================

    # url -> link publicado (afiliado quando existir);
    # url_original -> chave estável de histórico e anti-duplicação.
    produto = aplicar_afiliado(produto)

    # ========================================================
    # 2. IDENTIFICAR CATEGORIA
    # ========================================================

    categoria = identificar_categoria(
        produto["nome"]
    )

    produto["categoria"] = categoria

    # Nicho: 'outros' só passa se for produto de tecnologia.
    if categoria == "outros" and not eh_tecnologia(produto["nome"]):
        print(
            f"🚫 Fora do nicho de tecnologia: "
            f"{produto['nome'][:60]}"
        )

        return {"status": "fora_do_nicho"}

    print(
        f"🔎 Categoria identificada: "
        f"{categoria}"
    )

    # ========================================================
    # 3. ANALISAR OFERTA
    # ========================================================

    try:
        oferta = analisar_oferta(
            produto
        )

    except Exception as erro:
        print(
            f"❌ Erro analisando oferta "
            f"{produto['nome']}: {erro}"
        )

        return {
            "status": "erro",
            "motivo": str(erro)
        }

    preco_anterior = oferta.get(
        "preco_anterior"
    )

    preco_atual = oferta.get(
        "preco_atual"
    )

    desconto = oferta.get(
        "desconto",
        0
    )

    score = oferta.get(
        "score",
        0
    )

    print(
        f"⭐ Deal Score: "
        f"{score}/100"
    )

    # ========================================================
    # 4. DIAGNÓSTICO DOS PREÇOS
    # ========================================================

    print(
        f"💰 VALIDAÇÃO: "
        f"{oferta['nome']}"
    )

    print(
        f"   Preço anterior recebido: "
        f"{preco_anterior}"
    )

    print(
        f"   Preço atual recebido: "
        f"{preco_atual}"
    )

    print(
        f"   Desconto calculado: "
        f"{desconto}%"
    )

    # ========================================================
    # 5. SEGUNDA BARREIRA DE SEGURANÇA
    # ========================================================

    # --------------------------------------------------------
    # Preços ausentes
    # --------------------------------------------------------

    if (
        preco_anterior is None
        or preco_atual is None
    ):
        print(
            f"🚫 Preço ausente bloqueado: "
            f"{oferta['nome']}"
        )

        return {
            "status": "preco_invalido",
            "oferta": oferta
        }

    # --------------------------------------------------------
    # Garantir que sejam números
    # --------------------------------------------------------

    try:
        preco_anterior = float(
            preco_anterior
        )

        preco_atual = float(
            preco_atual
        )

        desconto = float(
            desconto
        )

    except (TypeError, ValueError):
        print(
            f"🚫 Formato de preço inválido: "
            f"{oferta['nome']}"
        )

        return {
            "status": "preco_invalido",
            "oferta": oferta
        }

    # --------------------------------------------------------
    # Preços zero/negativos
    # --------------------------------------------------------

    if (
        preco_anterior <= 0
        or preco_atual <= 0
    ):
        print(
            f"🚫 Preço zero ou negativo: "
            f"{oferta['nome']}"
        )

        return {
            "status": "preco_invalido",
            "oferta": oferta
        }

    # --------------------------------------------------------
    # Promoção precisa reduzir o preço
    # --------------------------------------------------------

    if preco_atual >= preco_anterior:
        print(
            f"🚫 Sem redução real de preço: "
            f"{oferta['nome']}"
        )

        print(
            f"   R$ {preco_anterior:.2f}"
            f" -> R$ {preco_atual:.2f}"
        )

        return {
            "status": "preco_invalido",
            "oferta": oferta
        }

    # --------------------------------------------------------
    # Validar desconto mínimo
    # --------------------------------------------------------

    if desconto < DESCONTO_MINIMO:
        print(
            f"🚫 Desconto insuficiente: "
            f"{oferta['nome']}"
        )

        print(
            f"   {desconto:.2f}% OFF"
        )

        return {
            "status": "desconto_insuficiente",
            "oferta": oferta
        }

    # --------------------------------------------------------
    # Proteção contra parcela/cupom interpretado como preço
    # --------------------------------------------------------

    if desconto > DESCONTO_MAXIMO:
        print(
            f"🚨 PREÇO SUSPEITO BLOQUEADO: "
            f"{oferta['nome']}"
        )

        print(
            f"   Preço anterior: "
            f"R$ {preco_anterior:.2f}"
        )

        print(
            f"   Preço interpretado: "
            f"R$ {preco_atual:.2f}"
        )

        print(
            f"   Desconto: "
            f"{desconto:.2f}%"
        )

        return {
            "status": "preco_suspeito",
            "oferta": oferta
        }

    # --------------------------------------------------------
    # Preço aprovado
    # --------------------------------------------------------

    print(
        f"🛡️ Preços validados: "
        f"R$ {preco_anterior:.2f}"
        f" -> R$ {preco_atual:.2f}"
        f" ({desconto:.2f}% OFF)"
    )

    # ========================================================
    # 6. SALVAR PRODUTO NO HISTÓRICO
    # ========================================================

    # Chave estável do produto: a URL original (o link de afiliado
    # pode mudar quando a conversão termina). O Discord usa oferta["url"].
    chave_url = oferta.get("url_original") or oferta["url"]

    salvar_produto(
        nome=oferta["nome"],
        categoria=oferta["categoria"],
        loja=oferta["loja"],
        preco_anterior=preco_anterior,
        preco_atual=preco_atual,
        url=chave_url,
        url_afiliado=(
            oferta["url"] if oferta["url"] != chave_url else None
        ),
        imagem_url=oferta.get(
            "imagem"
        ),
        score=score
    )

    # ========================================================
    # 7. DEAL SCORE
    # ========================================================

    if not oferta["publicar"]:
        print(
            f"❌ Oferta rejeitada pelo Deal Score: "
            f"{oferta['nome']}"
        )

        print(
            f"   Score: {score}/100"
        )

        return {
            "status": "rejeitada",
            "oferta": oferta
        }

    # ========================================================
    # 8. ANTI-DUPLICAÇÃO
    # ========================================================

    if oferta_ja_publicada(
        chave_url,
        preco_atual
    ):
        print(
            f"⏭️ Oferta duplicada ignorada: "
            f"{oferta['nome']}"
        )

        return {
            "status": "duplicada",
            "oferta": oferta
        }

    # ========================================================
    # 9. ESCOLHER CANAL
    # ========================================================

    canal_id = escolher_canal(
        oferta["categoria"]
    )

    if canal_id is None:
        print(
            f"⏸️ Sem canal configurado para "
            f"'{oferta['categoria']}' (defina CANAL_PC no .env): "
            f"{oferta['nome'][:60]}"
        )

        return {
            "status": "sem_canal",
            "oferta": oferta
        }

    print(
        f"📡 Canal escolhido: "
        f"{canal_id}"
    )

    # ========================================================
    # 10. PUBLICAR NO DISCORD
    # ========================================================

    enviado = await enviar_oferta(
        bot,
        canal_id,
        oferta
    )

    if not enviado:
        print(
            f"❌ Falha enviando oferta: "
            f"{oferta['nome']}"
        )

        return {
            "status": "erro_envio",
            "oferta": oferta
        }

    # ========================================================
    # 11. REGISTRAR PUBLICAÇÃO
    # ========================================================

    registrar_oferta_publicada(
        nome=oferta["nome"],
        url=chave_url,
        preco=preco_atual,
        canal_id=canal_id
    )

    try:
        await notificar_alertas(bot, oferta)

    except Exception as erro:
        print(f"⚠️ Falha ao notificar alertas: {erro}")

    print(
        f"🔥 PROCESSAMENTO CONCLUÍDO: "
        f"{oferta['nome']}"
    )

    return {
        "status": "publicada",
        "oferta": oferta,
        "canal_id": canal_id
    }