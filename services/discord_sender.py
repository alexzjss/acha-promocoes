import discord


async def enviar_oferta(bot, canal_id, oferta):
    canal = bot.get_channel(canal_id)

    if canal is None:
        print(f"❌ Canal {canal_id} não encontrado.")
        return False

    embed = discord.Embed(
        title=oferta["classificacao"],
        description=f"**{oferta['nome']}**",
        color=discord.Color.orange(),
        url=oferta["url"]
    )

    embed.add_field(
        name="💰 Preço",
        value=(
            f"~~R$ {oferta['preco_anterior']:.2f}~~\n"
            f"**R$ {oferta['preco_atual']:.2f}**"
        ),
        inline=True
    )

    embed.add_field(
        name="📉 Desconto",
        value=f"**{oferta['desconto']:.2f}% OFF**",
        inline=True
    )

    embed.add_field(
        name="⭐ Deal Score",
        value=f"**{oferta['score']}/100**",
        inline=True
    )

    embed.add_field(
        name="🏪 Loja",
        value=oferta["loja"],
        inline=True
    )

    if oferta.get("imagem"):
        embed.set_image(url=oferta["imagem"])

    embed.set_footer(
        text="🤖 Acha-Promoções • Monitoramento automático"
    )

    view = discord.ui.View()

    botao = discord.ui.Button(
        label="🛒 Ver promoção",
        url=oferta["url"],
        style=discord.ButtonStyle.link
    )

    view.add_item(botao)

    await canal.send(
        embed=embed,
        view=view
    )

    print(f"✅ Oferta enviada: {oferta['nome']}")

    return True