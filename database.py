import sqlite3
from pathlib import Path


DB_NAME = str(Path(__file__).resolve().parent / "promocoes.db")


# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

def conectar():
    return sqlite3.connect(DB_NAME)


# ============================================================
# CRIAÇÃO DAS TABELAS
# ============================================================

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    # Histórico de produtos encontrados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            loja TEXT NOT NULL,
            preco_anterior REAL,
            preco_atual REAL NOT NULL,
            url TEXT NOT NULL,
            imagem_url TEXT,
            score INTEGER DEFAULT 0,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Histórico das ofertas que realmente foram
    # publicadas no Discord
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ofertas_publicadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            url TEXT NOT NULL,
            preco REAL NOT NULL,
            canal_id INTEGER NOT NULL,
            publicado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migração: link de afiliado publicado (a coluna url guarda a
    # URL original, usada como chave de histórico e anti-duplicação).
    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN url_afiliado TEXT")

    except sqlite3.OperationalError:
        pass  # coluna já existe

    # Alertas por palavra-chave (comando /alerta)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            palavras TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, palavras)
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Banco SQLite criado/verificado com sucesso!")


# ============================================================
# VERIFICA SE UMA OFERTA JÁ FOI PUBLICADA
# ============================================================

def oferta_ja_publicada(url, preco):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM ofertas_publicadas
        WHERE url = ?
        AND preco = ?
        LIMIT 1
    """, (
        url,
        preco
    ))

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


# ============================================================
# REGISTRA UMA OFERTA PUBLICADA
# ============================================================

def registrar_oferta_publicada(
    nome,
    url,
    preco,
    canal_id
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ofertas_publicadas (
            nome,
            url,
            preco,
            canal_id
        )
        VALUES (?, ?, ?, ?)
    """, (
        nome,
        url,
        preco,
        canal_id
    ))

    conn.commit()
    conn.close()

    print(
        f"💾 Oferta registrada no banco: {nome}"
    )


# ============================================================
# SALVA PRODUTO NO HISTÓRICO
# ============================================================

def salvar_produto(
    nome,
    categoria,
    loja,
    preco_anterior,
    preco_atual,
    url,
    imagem_url=None,
    score=0,
    url_afiliado=None
):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos (
            nome,
            categoria,
            loja,
            preco_anterior,
            preco_atual,
            url,
            imagem_url,
            score,
            url_afiliado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome,
        categoria,
        loja,
        preco_anterior,
        preco_atual,
        url,
        imagem_url,
        score,
        url_afiliado
    ))

    conn.commit()
    conn.close()

    print(
        f"📦 Produto salvo no histórico: {nome}"
    )


# ============================================================
# LISTA PRODUTOS
# ============================================================

def listar_produtos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM produtos
        ORDER BY data_coleta DESC
    """)

    produtos = cursor.fetchall()

    conn.close()

    return produtos


# ============================================================
# LISTA OFERTAS JÁ PUBLICADAS
# ============================================================

def listar_ofertas_publicadas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM ofertas_publicadas
        ORDER BY publicado_em DESC
    """)

    ofertas = cursor.fetchall()

    conn.close()

    return ofertas


# ============================================================
# RANKING DE MELHORES OFERTAS
# ============================================================

ORDENS = {
    "desconto": "desconto_pct DESC, economia DESC",
    "economia": "economia DESC, desconto_pct DESC",
    "preco": "preco_atual ASC, desconto_pct DESC",
    "score": "score DESC, desconto_pct DESC",
}

PERIODOS_HORAS = {
    "24h": 24,
    "7d": 24 * 7,
    "tudo": None,
}


def buscar_melhores(
    ordem="desconto",
    categoria=None,
    loja=None,
    preco_max=None,
    periodo="24h",
    limite=5,
    offset=0,
    excluir_outros=True
):
    """
    Retorna (total, linhas): uma linha por produto (a coleta mais
    recente de cada URL), ordenada pelo critério escolhido.
    """

    if ordem not in ORDENS:
        ordem = "desconto"

    horas = PERIODOS_HORAS.get(periodo, 24)

    parametros = []
    filtro_periodo = ""

    if horas is not None:
        filtro_periodo = "WHERE data_coleta >= datetime('now', ?)"
        parametros.append(f"-{horas} hours")

    filtros = ["preco_anterior > preco_atual", "preco_anterior > 0"]

    if categoria:
        filtros.append("categoria = ?")
        parametros.append(categoria)

    elif excluir_outros:
        filtros.append("COALESCE(categoria, 'outros') != 'outros'")

    if loja:
        filtros.append("loja = ?")
        parametros.append(loja)

    if preco_max is not None:
        filtros.append("preco_atual <= ?")
        parametros.append(preco_max)

    base = f"""
        FROM (
            SELECT p.*,
                   COALESCE(p.url_afiliado, p.url) AS link,
                   (p.preco_anterior - p.preco_atual) AS economia,
                   (p.preco_anterior - p.preco_atual)
                       * 100.0 / p.preco_anterior AS desconto_pct,
                   (SELECT MIN(h.preco_atual) FROM produtos h
                     WHERE h.url = p.url) AS menor_preco,
                   (SELECT MAX(h.preco_atual) FROM produtos h
                     WHERE h.url = p.url) AS maior_preco,
                   (SELECT COUNT(*) FROM produtos h
                     WHERE h.url = p.url) AS observacoes
            FROM produtos p
            JOIN (
                SELECT MAX(id) AS mid
                FROM produtos
                {filtro_periodo}
                GROUP BY url
            ) ultimo ON p.id = ultimo.mid
        )
        WHERE {" AND ".join(filtros)}
    """

    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) {base}", parametros)
    total = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT * {base} ORDER BY {ORDENS[ordem]} LIMIT ? OFFSET ?",
        parametros + [limite, offset]
    )

    linhas = [dict(linha) for linha in cursor.fetchall()]

    conn.close()

    return total, linhas


def listar_lojas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT loja FROM produtos ORDER BY loja")

    lojas = [linha[0] for linha in cursor.fetchall()]

    conn.close()

    return lojas


# ============================================================
# ALERTAS POR PALAVRA-CHAVE
# ============================================================

def adicionar_alerta(user_id, palavras):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO alertas (user_id, palavras) VALUES (?, ?)",
        (user_id, palavras.lower().strip())
    )

    criado = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return criado


def remover_alerta(user_id, palavras):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM alertas WHERE user_id = ? AND palavras = ?",
        (user_id, palavras.lower().strip())
    )

    removido = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return removido


def listar_alertas(user_id=None):
    conn = conectar()
    cursor = conn.cursor()

    if user_id is None:
        cursor.execute("SELECT user_id, palavras FROM alertas")
    else:
        cursor.execute(
            "SELECT user_id, palavras FROM alertas WHERE user_id = ?",
            (user_id,)
        )

    alertas = cursor.fetchall()

    conn.close()

    return alertas


# ============================================================
# TESTE DO BANCO
# ============================================================

if __name__ == "__main__":
    criar_banco()

    print("\n📦 PRODUTOS CADASTRADOS")
    print("=" * 60)

    produtos = listar_produtos()

    for produto in produtos:
        print(produto)

    print("\n🔥 OFERTAS PUBLICADAS")
    print("=" * 60)

    ofertas = listar_ofertas_publicadas()

    for oferta in ofertas:
        print(oferta)