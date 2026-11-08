import os

from flask import Flask, request, render_template_string


app = Flask(__name__)


PAGINA_INICIAL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>Acha-Promoções OAuth</title>

    <style>
        body {
            background: #111827;
            color: #f9fafb;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 700px;
            margin: 40px auto;
            padding: 30px;
            background: #1f2937;
            border-radius: 14px;
        }

        h1 {
            color: #facc15;
        }

        code {
            display: block;
            padding: 15px;
            margin-top: 15px;
            background: #0f172a;
            color: #4ade80;
            overflow-wrap: anywhere;
            border-radius: 8px;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>🤖 Acha-Promoções</h1>

        <p>
            Callback OAuth do Mercado Livre disponível.
        </p>

        <p>
            Acesse a URL de autorização para conectar
            sua conta do Mercado Livre.
        </p>
    </div>
</body>
</html>
"""


PAGINA_SUCESSO = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>Autorização concluída</title>

    <style>
        body {
            background: #111827;
            color: #f9fafb;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 700px;
            margin: 40px auto;
            padding: 30px;
            background: #1f2937;
            border-radius: 14px;
        }

        h1 {
            color: #4ade80;
        }

        code {
            display: block;
            padding: 15px;
            margin-top: 15px;
            background: #0f172a;
            color: #facc15;
            overflow-wrap: anywhere;
            border-radius: 8px;
        }

        .aviso {
            color: #fca5a5;
            font-weight: bold;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>✅ Autorização recebida</h1>

        <p>
            O Mercado Livre retornou o código de autorização.
        </p>

        <p>
            Copie o código abaixo:
        </p>

        <code>{{ code }}</code>

        <p class="aviso">
            Não compartilhe esse código e não publique em prints.
        </p>

        <p>
            Agora volte ao terminal para trocar esse código
            pelo Access Token.
        </p>
    </div>
</body>
</html>
"""


PAGINA_ERRO = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>Erro na autorização</title>

    <style>
        body {
            background: #111827;
            color: #f9fafb;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 700px;
            margin: 40px auto;
            padding: 30px;
            background: #1f2937;
            border-radius: 14px;
        }

        h1 {
            color: #f87171;
        }

        code {
            display: block;
            padding: 15px;
            margin-top: 15px;
            background: #0f172a;
            color: #fca5a5;
            overflow-wrap: anywhere;
            border-radius: 8px;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>❌ Falha na autorização</h1>

        <p>{{ mensagem }}</p>
    </div>
</body>
</html>
"""


@app.route("/")
def inicio():
    return render_template_string(PAGINA_INICIAL)


@app.route("/health")
def health():
    return {
        "status": "ok",
        "servico": "acha-promocoes-oauth"
    }, 200


@app.route("/callback")
def callback():
    erro = request.args.get("error")
    descricao_erro = request.args.get(
        "error_description",
        ""
    )

    if erro:
        return render_template_string(
            PAGINA_ERRO,
            mensagem=(
                f"O Mercado Livre retornou o erro "
                f"'{erro}'. {descricao_erro}"
            )
        ), 400

    codigo = request.args.get("code")
    state_recebido = request.args.get("state")
    state_esperado = os.getenv("OAUTH_STATE")

    if not codigo:
        return render_template_string(
            PAGINA_ERRO,
            mensagem=(
                "Nenhum código de autorização foi "
                "recebido pelo callback."
            )
        ), 400

    if not state_esperado:
        return render_template_string(
            PAGINA_ERRO,
            mensagem=(
                "A variável OAUTH_STATE não foi "
                "configurada no Render."
            )
        ), 500

    if state_recebido != state_esperado:
        return render_template_string(
            PAGINA_ERRO,
            mensagem=(
                "O parâmetro state recebido não corresponde "
                "ao state configurado. A autorização foi "
                "bloqueada por segurança."
            )
        ), 403

    return render_template_string(
        PAGINA_SUCESSO,
        code=codigo
    )


if __name__ == "__main__":
    porta = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=porta
    )