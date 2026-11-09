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
    score=0
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
            score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nome,
        categoria,
        loja,
        preco_anterior,
        preco_atual,
        url,
        imagem_url,
        score
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