import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DB_PATH = DATA_DIR / "afiliados.db"


# ============================================================
# CONEXÃO
# ============================================================

def conectar():
    conexao = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conexao.row_factory = sqlite3.Row

    return conexao


# ============================================================
# INICIALIZAR BANCO
# ============================================================

def inicializar_banco():
    with conectar() as conexao:

        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS links_afiliados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                loja TEXT NOT NULL,

                item_id TEXT NOT NULL,

                url_original TEXT NOT NULL,

                url_afiliado TEXT,

                status TEXT NOT NULL DEFAULT 'pendente',

                tentativas INTEGER NOT NULL DEFAULT 0,

                ultimo_erro TEXT,

                criado_em TEXT NOT NULL,

                atualizado_em TEXT NOT NULL,

                convertido_em TEXT,

                UNIQUE(loja, item_id)
            )
            """
        )

        conexao.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_links_afiliados_status
            ON links_afiliados(status)
            """
        )

        conexao.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_links_afiliados_item
            ON links_afiliados(item_id)
            """
        )

        conexao.commit()


# ============================================================
# ADICIONAR URL À FILA
# ============================================================

def adicionar_url(
    loja,
    item_id,
    url_original
):
    agora = datetime.now().isoformat(
        timespec="seconds"
    )

    with conectar() as conexao:

        conexao.execute(
            """
            INSERT INTO links_afiliados (
                loja,
                item_id,
                url_original,
                status,
                criado_em,
                atualizado_em
            )
            VALUES (?, ?, ?, 'pendente', ?, ?)

            ON CONFLICT(loja, item_id)
            DO UPDATE SET
                url_original = excluded.url_original,
                atualizado_em = excluded.atualizado_em
            """,
            (
                loja,
                item_id,
                url_original,
                agora,
                agora
            )
        )

        conexao.commit()


# ============================================================
# BUSCAR URL AFILIADA
# ============================================================

def buscar_url_afiliada(
    loja,
    item_id
):
    with conectar() as conexao:

        resultado = conexao.execute(
            """
            SELECT url_afiliado
            FROM links_afiliados

            WHERE loja = ?
            AND item_id = ?
            AND status = 'convertido'
            AND url_afiliado IS NOT NULL

            LIMIT 1
            """,
            (
                loja,
                item_id
            )
        ).fetchone()

    if not resultado:
        return None

    return resultado["url_afiliado"]


# ============================================================
# BUSCAR PENDENTES
# ============================================================

def buscar_pendentes(
    limite=20
):
    with conectar() as conexao:

        resultados = conexao.execute(
            """
            SELECT
                id,
                loja,
                item_id,
                url_original,
                tentativas

            FROM links_afiliados

            WHERE status = 'pendente'

            ORDER BY criado_em ASC

            LIMIT ?
            """,
            (limite,)
        ).fetchall()

    return [
        dict(resultado)
        for resultado in resultados
    ]


# ============================================================
# MARCAR COMO CONVERTIDO
# ============================================================

def marcar_convertido(
    loja,
    item_id,
    url_afiliado
):
    agora = datetime.now().isoformat(
        timespec="seconds"
    )

    with conectar() as conexao:

        conexao.execute(
            """
            UPDATE links_afiliados

            SET
                url_afiliado = ?,
                status = 'convertido',
                ultimo_erro = NULL,
                atualizado_em = ?,
                convertido_em = ?

            WHERE loja = ?
            AND item_id = ?
            """,
            (
                url_afiliado,
                agora,
                agora,
                loja,
                item_id
            )
        )

        conexao.commit()


# ============================================================
# REGISTRAR ERRO
# ============================================================

def registrar_erro(
    loja,
    item_id,
    erro
):
    agora = datetime.now().isoformat(
        timespec="seconds"
    )

    with conectar() as conexao:

        conexao.execute(
            """
            UPDATE links_afiliados

            SET
                tentativas = tentativas + 1,
                ultimo_erro = ?,
                atualizado_em = ?

            WHERE loja = ?
            AND item_id = ?
            """,
            (
                str(erro),
                agora,
                loja,
                item_id
            )
        )

        conexao.commit()


# ============================================================
# FALLBACK DA URL
# ============================================================

def obter_url_publicacao(
    loja,
    item_id,
    url_original
):
    """
    Retorna URL afiliada quando disponível.

    Caso contrário, retorna a URL original.
    """

    url_afiliado = buscar_url_afiliada(
        loja,
        item_id
    )

    return (
        url_afiliado
        or url_original
    )


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    inicializar_banco()

    print(
        "✅ Banco de afiliados inicializado."
    )

    print(
        f"📁 Banco: {DB_PATH}"
    )