"""
Comandos de consulta do bot:

  /melhores  (ou !melhores)  ranking das melhores ofertas
  /alerta    (ou !alerta)    avisa por DM quando surgir oferta com a palavra
  /alertas                   lista seus alertas
  /remover_alerta            remove um alerta

As respostas dos slash commands são efêmeras (só quem chamou vê).
Os comandos com prefixo respondem por DM, já que mensagens comuns
não podem ser privadas no canal.
"""

import discord
from discord import app_commands
from discord.ext import commands

from database import (
    adicionar_alerta,
    buscar_melhores,
    listar_alertas,
    listar_lojas,
    remover_alerta,
)


POR_PAGINA = 5

ROTULOS_ORDEM = {
    "desconto": "📉 Maior % de desconto",
    "economia": "💸 Maior economia em R$",
    "preco": "🏷️ Menor preço",
    "score": "⭐ Maior Deal Score",
}

ROTULOS_PERIODO = {
    "24h": "últimas 24h",
    "7d": "últimos 7 dias",
    "tudo": "todo o histórico",
}

CATEGORIAS = [
    "placa_video",
    "processador",
    "placa_mae",
    "ram",
    "ssd_hd",
    "fonte",
    "cooler",
    "gabinete",
    "monitor",
    "acessorios",
    "action_figures",
    "outros",
]

# Apelidos aceitos no comando com prefixo.
APELIDOS = {
    "ordem": {
        "%": "desconto", "desconto": "desconto", "porcentagem": "desconto",
        "economia": "economia", "reais": "economia", "total": "economia",
        "preco": "preco", "preço": "preco", "barato": "preco",
        "score": "score", "nota": "score",
    },
    "periodo": {
        "24h": "24h", "hoje": "24h", "dia": "24h",
        "7d": "7d", "semana": "7d",
        "tudo": "tudo", "todos": "tudo",
    },
}


def brl(valor):
    texto = f"{valor:,.2f}"

    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def historico(item):
    """Compara o preço atual com o histórico registrado pelo bot."""

    if item.get("observacoes", 0) < 2:
        return ""

    menor = item["menor_preco"]
    maior = item["maior_preco"]

    # Preço nunca mudou desde a primeira coleta: nada a afirmar.
    if maior == menor:
        return ""

    if item["preco_atual"] <= menor:
        return f"\n🏅 **menor preço já registrado** (já esteve {brl(maior)})"

    return f"\n📊 menor preço visto: {brl(menor)}"


def montar_embed(estado, total, linhas):
    pagina = estado["pagina"]
    paginas = max(1, -(-total // POR_PAGINA))

    embed = discord.Embed(
        title="🏆 Melhores promoções",
        color=discord.Color.orange(),
    )

    filtros = [
        ROTULOS_ORDEM[estado["ordem"]],
        ROTULOS_PERIODO[estado["periodo"]],
    ]

    if estado["categoria"]:
        filtros.append(f"categoria: {estado['categoria']}")

    else:
        filtros.append("sem 'outros'")

    if estado["loja"]:
        filtros.append(f"loja: {estado['loja']}")

    if estado["preco_max"] is not None:
        filtros.append(f"até {brl(estado['preco_max'])}")

    embed.set_footer(
        text=f"{' • '.join(filtros)} • página {pagina + 1}/{paginas} "
             f"• {total} ofertas"
    )

    if not linhas:
        embed.description = (
            "Nenhuma oferta encontrada com esses filtros. "
            "Tente ampliar o período ou remover filtros."
        )
        return embed

    blocos = []

    for posicao, item in enumerate(
        linhas, start=pagina * POR_PAGINA + 1
    ):
        blocos.append(
            f"**{posicao}. [{item['nome'][:90]}]({item['url']})**\n"
            f"🏬 {item['loja']} • ~~{brl(item['preco_anterior'])}~~ → "
            f"**{brl(item['preco_atual'])}**\n"
            f"📉 **{item['desconto_pct']:.1f}% OFF** • "
            f"💸 economia {brl(item['economia'])} • "
            f"⭐ {item['score']}/100{historico(item)}"
        )

    embed.description = "\n\n".join(blocos)

    if linhas[0].get("imagem_url"):
        embed.set_thumbnail(url=linhas[0]["imagem_url"])

    return embed


def consultar(estado):
    return buscar_melhores(
        ordem=estado["ordem"],
        categoria=estado["categoria"],
        loja=estado["loja"],
        preco_max=estado["preco_max"],
        periodo=estado["periodo"],
        limite=POR_PAGINA,
        offset=estado["pagina"] * POR_PAGINA,
    )


class OrdemSelect(discord.ui.Select):
    def __init__(self, atual):
        super().__init__(
            placeholder="Ordenar por...",
            options=[
                discord.SelectOption(
                    label=rotulo, value=chave, default=(chave == atual)
                )
                for chave, rotulo in ROTULOS_ORDEM.items()
            ],
        )

    async def callback(self, interaction):
        view = self.view
        view.estado["ordem"] = self.values[0]
        view.estado["pagina"] = 0

        await view.atualizar(interaction)


class RankingView(discord.ui.View):
    def __init__(self, estado, autor_id, total):
        super().__init__(timeout=300)

        self.estado = estado
        self.autor_id = autor_id
        self.total = total
        self.message = None

        self.add_item(OrdemSelect(estado["ordem"]))
        self._ajustar_botoes()

    def _ajustar_botoes(self):
        paginas = max(1, -(-self.total // POR_PAGINA))

        self.anterior.disabled = self.estado["pagina"] <= 0
        self.proxima.disabled = self.estado["pagina"] >= paginas - 1

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message(
                "Use /melhores para ver o seu próprio ranking.",
                ephemeral=True,
            )
            return False

        return True

    async def atualizar(self, interaction):
        total, linhas = consultar(self.estado)

        self.total = total

        for item in self.children:
            if isinstance(item, OrdemSelect):
                for opcao in item.options:
                    opcao.default = opcao.value == self.estado["ordem"]

        self._ajustar_botoes()

        await interaction.response.edit_message(
            embed=montar_embed(self.estado, total, linhas),
            view=self,
        )

    @discord.ui.button(label="◀ Anterior", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction, button):
        self.estado["pagina"] = max(0, self.estado["pagina"] - 1)

        await self.atualizar(interaction)

    @discord.ui.button(label="Próxima ▶", style=discord.ButtonStyle.secondary)
    async def proxima(self, interaction, button):
        self.estado["pagina"] += 1

        await self.atualizar(interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)

            except discord.HTTPException:
                pass


def estado_inicial(
    ordem="desconto",
    categoria=None,
    loja=None,
    preco_max=None,
    periodo="24h",
):
    return {
        "ordem": ordem,
        "categoria": categoria,
        "loja": loja,
        "preco_max": preco_max,
        "periodo": periodo,
        "pagina": 0,
    }


class Consultas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------------------------------------------------------
    # /melhores
    # --------------------------------------------------------

    @app_commands.command(
        name="melhores",
        description="Mostra as melhores promoções coletadas pelo bot",
    )
    @app_commands.describe(
        ordem="Critério de ordenação",
        periodo="Período da coleta",
        categoria="Filtrar por categoria",
        loja="Filtrar por loja (ex.: KaBuM!, Pichau)",
        preco_max="Preço máximo em R$",
    )
    @app_commands.choices(
        ordem=[
            app_commands.Choice(name=r, value=k)
            for k, r in ROTULOS_ORDEM.items()
        ],
        periodo=[
            app_commands.Choice(name=r, value=k)
            for k, r in ROTULOS_PERIODO.items()
        ],
        categoria=[
            app_commands.Choice(name=c, value=c) for c in CATEGORIAS
        ],
    )
    async def melhores(
        self,
        interaction: discord.Interaction,
        ordem: str = "desconto",
        periodo: str = "24h",
        categoria: str | None = None,
        loja: str | None = None,
        preco_max: app_commands.Range[float, 1] | None = None,
    ):
        estado = estado_inicial(ordem, categoria, loja, preco_max, periodo)

        total, linhas = consultar(estado)

        view = RankingView(estado, interaction.user.id, total)

        await interaction.response.send_message(
            embed=montar_embed(estado, total, linhas),
            view=view,
            ephemeral=True,
        )

        view.message = await interaction.original_response()

    @melhores.autocomplete("loja")
    async def autocompletar_loja(self, interaction, atual: str):
        return [
            app_commands.Choice(name=l, value=l)
            for l in listar_lojas()
            if atual.lower() in l.lower()
        ][:25]

    # --------------------------------------------------------
    # !melhores [ordem] [periodo] [categoria]
    # --------------------------------------------------------

    @commands.command(name="melhores")
    async def melhores_prefixo(self, ctx, *argumentos):
        estado = estado_inicial()

        for argumento in argumentos:
            chave = argumento.lower()

            if chave in APELIDOS["ordem"]:
                estado["ordem"] = APELIDOS["ordem"][chave]

            elif chave in APELIDOS["periodo"]:
                estado["periodo"] = APELIDOS["periodo"][chave]

            elif chave in CATEGORIAS:
                estado["categoria"] = chave

            else:
                try:
                    estado["preco_max"] = float(chave.replace(",", "."))

                except ValueError:
                    estado["loja"] = argumento

        total, linhas = consultar(estado)

        view = RankingView(estado, ctx.author.id, total)
        embed = montar_embed(estado, total, linhas)

        try:
            view.message = await ctx.author.send(embed=embed, view=view)

            if ctx.guild:
                await ctx.message.add_reaction("📬")

        except discord.Forbidden:
            view.message = await ctx.send(
                "⚠️ Não consegui enviar por DM; usando o canal.",
                embed=embed,
                view=view,
            )

    # --------------------------------------------------------
    # Alertas
    # --------------------------------------------------------

    @app_commands.command(
        name="alerta",
        description="Receba uma DM quando surgir oferta com estas palavras",
    )
    @app_commands.describe(palavras="Ex.: rtx 4060 ou ryzen 5600")
    async def alerta(self, interaction: discord.Interaction, palavras: str):
        palavras = palavras.strip()

        if len(palavras) < 3:
            await interaction.response.send_message(
                "Use pelo menos 3 caracteres.", ephemeral=True
            )
            return

        criado = adicionar_alerta(interaction.user.id, palavras)

        await interaction.response.send_message(
            f"🔔 Alerta criado: **{palavras}**. Avisarei por DM "
            "(mantenha as DMs do servidor liberadas)."
            if criado
            else f"Você já tem o alerta **{palavras}**.",
            ephemeral=True,
        )

    @commands.command(name="alerta")
    async def alerta_prefixo(self, ctx, *, palavras: str):
        criado = adicionar_alerta(ctx.author.id, palavras)

        await ctx.reply(
            f"🔔 Alerta criado: **{palavras}**."
            if criado
            else f"Você já tem o alerta **{palavras}**.",
            mention_author=False,
        )

    @app_commands.command(
        name="alertas", description="Lista os seus alertas"
    )
    async def alertas(self, interaction: discord.Interaction):
        meus = [p for _, p in listar_alertas(interaction.user.id)]

        await interaction.response.send_message(
            "🔔 Seus alertas:\n" + "\n".join(f"• {p}" for p in meus)
            if meus
            else "Você não tem alertas. Crie um com /alerta.",
            ephemeral=True,
        )

    @app_commands.command(
        name="remover_alerta", description="Remove um dos seus alertas"
    )
    async def remover_alerta_cmd(
        self, interaction: discord.Interaction, palavras: str
    ):
        removido = remover_alerta(interaction.user.id, palavras)

        await interaction.response.send_message(
            "🗑️ Alerta removido." if removido else "Alerta não encontrado.",
            ephemeral=True,
        )

    @remover_alerta_cmd.autocomplete("palavras")
    async def autocompletar_alerta(self, interaction, atual: str):
        return [
            app_commands.Choice(name=p, value=p)
            for _, p in listar_alertas(interaction.user.id)
            if atual.lower() in p
        ][:25]


async def setup(bot):
    await bot.add_cog(Consultas(bot))
