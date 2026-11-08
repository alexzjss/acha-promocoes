import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import criar_banco
from services.deal_processor import processar_produto
from services.scheduler import iniciar_scheduler

from database import (
    criar_banco,
    oferta_ja_publicada,
    registrar_oferta_publicada,
    salvar_produto
)


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    criar_banco()

    iniciar_scheduler(bot)

    print("------------------------------")
    print("🔥 BOT DE PROMOÇÕES ONLINE!")
    print(f"🤖 Bot: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print("------------------------------")

@bot.command()
async def testar(ctx):
    produto = {
        "nome": "Logitech G502 HERO Gaming Mouse",
        "loja": "Loja de teste",
        "preco_anterior": 399.90,
        "preco_atual": 249.90,
        "url": "https://example.com/produto-002",
        "imagem": None
    }

    resultado = await processar_produto(
        bot,
        produto
    )

    status = resultado["status"]

    if status == "duplicada":
        await ctx.send(
            "🛑 Essa oferta já foi publicada nesse preço."
        )

    elif status == "rejeitada":
        oferta = resultado["oferta"]

        await ctx.send(
            f"❌ Oferta rejeitada. "
            f"Score: {oferta['score']}/100"
        )

    elif status == "erro":
        await ctx.send(
            f"❌ Produto inválido: "
            f"{resultado['motivo']}"
        )

    elif status == "erro_envio":
        await ctx.send(
            "❌ Não consegui publicar essa oferta."
        )


if TOKEN is None:
    raise ValueError(
        "DISCORD_TOKEN não foi encontrado no arquivo .env"
    )


bot.run(TOKEN)