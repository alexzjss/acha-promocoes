"""
Registro dos coletores. Cada entrada é (nome, caminho "módulo:função").
A função deve ser async e aceitar `limite`; os módulos só são
importados quando o coletor é executado, assim uma dependência
faltando em uma loja não derruba as outras.
"""

COLETORES = [
    ("KaBuM!", "collectors.kabum:buscar_ofertas_kabum"),
    ("Mercado Livre", "collectors.mercado_livre:coletar_ofertas"),
    ("Pichau", "collectors.pichau:buscar_ofertas_pichau"),
    ("Terabyte", "collectors.terabyte:buscar_ofertas_terabyte"),
    ("Magalu", "collectors.magalu:buscar_ofertas_magalu"),
    ("Amazon", "collectors.amazon:buscar_ofertas_amazon"),
]
