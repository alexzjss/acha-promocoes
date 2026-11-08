def calcular_desconto(preco_anterior, preco_atual):
    if preco_anterior <= 0:
        return 0

    if preco_atual <= 0:
        return 0

    if preco_atual >= preco_anterior:
        return 0

    desconto = (
        (preco_anterior - preco_atual)
        / preco_anterior
    ) * 100

    return round(desconto, 2)


def calcular_score(preco_anterior, preco_atual):
    desconto = calcular_desconto(
        preco_anterior,
        preco_atual
    )

    # Score inicial baseado no desconto
    if desconto >= 50:
        score = 100

    elif desconto >= 40:
        score = 95

    elif desconto >= 30:
        score = 85

    elif desconto >= 20:
        score = 75

    elif desconto >= 15:
        score = 65

    elif desconto >= 10:
        score = 50

    else:
        score = 30

    return score


def classificar_oferta(score):
    if score >= 95:
        return "🚨 OFERTA INSANA"

    elif score >= 85:
        return "🔥 OFERTA EXCELENTE"

    elif score >= 70:
        return "✅ BOA OFERTA"

    elif score >= 50:
        return "👀 OFERTA INTERESSANTE"

    else:
        return "❌ OFERTA FRACA"


def deve_publicar(score):
    return score >= 70


def analisar_oferta(produto):
    preco_anterior = produto["preco_anterior"]
    preco_atual = produto["preco_atual"]

    desconto = calcular_desconto(
        preco_anterior,
        preco_atual
    )

    score = calcular_score(
        preco_anterior,
        preco_atual
    )

    classificacao = classificar_oferta(score)

    publicar = deve_publicar(score)

    return {
        **produto,
        "desconto": desconto,
        "score": score,
        "classificacao": classificacao,
        "publicar": publicar
    }


# TESTE
if __name__ == "__main__":

    produto_teste = {
        "nome": "Logitech G502 HERO",
        "categoria": "Mouse",
        "loja": "Loja de teste",
        "preco_anterior": 399.90,
        "preco_atual": 249.90,
        "url": "https://example.com/produto",
        "imagem": None
    }

    oferta = analisar_oferta(produto_teste)

    print("\n🔥 ANÁLISE DA OFERTA")
    print("=" * 45)

    print("Produto:", oferta["nome"])
    print("Preço anterior: R$", oferta["preco_anterior"])
    print("Preço atual: R$", oferta["preco_atual"])
    print("Desconto:", oferta["desconto"], "%")
    print("Score:", oferta["score"], "/ 100")
    print("Classificação:", oferta["classificacao"])
    print("Publicar:", oferta["publicar"])