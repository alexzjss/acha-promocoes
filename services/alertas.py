import unicodedata

import discord

from database import listar_alertas


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())

    return "".join(c for c in texto if not unicodedata.combining(c))


def alerta_combina(palavras, nome):
    """Todas as palavras do alerta precisam aparecer no nome."""

    nome = _normalizar(nome)

    return all(p in nome for p in _normalizar(palavras).split())


async def notificar_alertas(bot, oferta):
    """Envia DM aos usuários cujo alerta combina com a oferta publicada."""

    avisados = set()

    for user_id, palavras in listar_alertas():
        if user_id in avisados:
            continue

        if not alerta_combina(palavras, oferta["nome"]):
            continue

        embed = discord.Embed(
            title=f"🔔 Alerta: {palavras}",
            description=(
                f"**[{oferta['nome']}]({oferta['url']})**\n"
                f"~~R$ {oferta['preco_anterior']:.2f}~~ → "
                f"**R$ {oferta['preco_atual']:.2f}** "
                f"({oferta['desconto']:.1f}% OFF) • {oferta['loja']}"
            ),
            color=discord.Color.gold(),
        )

        try:
            usuario = bot.get_user(user_id) or await bot.fetch_user(user_id)

            await usuario.send(embed=embed)

            avisados.add(user_id)

        except (discord.HTTPException, discord.Forbidden) as erro:
            print(f"⚠️ Não consegui avisar o usuário {user_id}: {erro}")
