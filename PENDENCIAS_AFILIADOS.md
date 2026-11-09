# Pendências: links de afiliados

Estado: a camada de afiliados está implementada, mas ainda **não foi commitada**
e a parte do Mercado Livre **não foi testada com login real**. Este documento
lista o que falta para colocar tudo em produção.

## O que já existe (código)

- `services/afiliados.py` — aplica o afiliado a todas as lojas (chamado em
  `services/deal_processor.py`). Gera o link na hora para Amazon (`tag=`) e para
  lojas com modelo de URL no `.env`; registra o Mercado Livre na fila.
- `services/afiliados_conversor.py` — converte a fila. Para o Mercado Livre usa o
  gerador do portal de Afiliados com sessão logada (Playwright, headless).
- `services/afiliados_db.py` — fila em `data/afiliados.db` (status `pendente` /
  `convertido`, contador de tentativas).
- `services/scheduler.py` — chama `converter_pendentes()` a cada ciclo, antes de publicar.
- `scripts/login_afiliados_ml.py` — abre um navegador visível para o login (uma vez).

Já testado (banco temporário): tag da Amazon, modelo de rede, loja sem afiliado,
produto repetido, aviso de falta de login do ML.

## O que falta fazer

### 1. Credenciais e configuração (.env)

Pedir ao dono da conta os dados e preencher o `.env` (nunca commitar):

```
AMAZON_ASSOCIATE_TAG=seu-id-20
AFILIADO_TEMPLATE_KABUM=https://rede.exemplo/deeplink?id=SEU_ID&u={url_codificada}
AFILIADO_TEMPLATE_TERABYTE=...
AFILIADO_TEMPLATE_PICHAU=...
AFILIADO_TEMPLATE_MAGALU=...
```

- Marcadores aceitos: `{url}` e `{url_codificada}`.
- Descobrir qual rede cada loja usa (Awin, Lomadee, Afilio, programa próprio) e
  copiar o formato de deeplink do painel da rede.
- Loja sem modelo configurado continua publicando o link original (sem erro).

### 2. Login no portal de Afiliados do Mercado Livre

1. `python scripts/login_afiliados_ml.py`
2. Entrar na conta de afiliado na janela que abrir e fechar a janela.
3. A sessão fica em `data/perfil_ml_afiliados/` (já ignorada pelo git via
   `data/`? **conferir o `.gitignore`**; se não estiver, adicionar `data/`).

### 3. Validar o gerador de links do ML (parte mais arriscada)

Os seletores em `gerar_link_ml()` (`services/afiliados_conversor.py`) são
genéricos, pois o portal exige login e não foi inspecionado:

- campo de texto visível → URL do produto;
- botão cujo nome contém "gerar";
- resultado lido por regex `meli.la/...` (ou `mercadolivre.com/sec/...`) no texto
  da página e nos valores de `input`/`textarea`.

Testar com a sessão logada:

```
python services/afiliados_conversor.py
```

Esperado: `🔗 Link afiliado ML gerado: https://meli.la/...` para cada pendente
(a fila tem dezenas de itens `pendente` após os ciclos do bot). Se falhar:

- abrir o portal logado, inspecionar a página do gerador e ajustar os
  seletores/regex; confirmar a URL real do gerador (`URL_GERADOR_ML`);
- verificar se o gerador aceita a URL de catálogo
  `https://www.mercadolivre.com.br/p/MLB...?pdp_filters=item_id:...` (formato
  usado pelo coletor). Se recusar, trocar por outro formato de URL.
- Verificar limites do portal (quantidade de links por hora); ajustar
  `limite` em `converter_pendentes()` no scheduler e a espera entre itens.

### 4. Teste ponta a ponta

1. Subir o bot (`python bot.py`) e esperar um ciclo completo.
2. No log, conferir a linha `🔗 Links de afiliado convertidos: N`.
3. No Discord, conferir que as ofertas novas saem com link afiliado
   (Amazon com `tag=`, ML com `meli.la`, lojas com o deeplink da rede).
4. Conferir `/melhores`: o link exibido deve ser o afiliado quando existir.
5. Reexecutar um ciclo: ofertas já publicadas **não** devem sair duplicadas
   (a chave é a URL original; o link afiliado fica em `produtos.url_afiliado`).

### 5. Itens publicados antes da conversão

Ofertas já postadas com link original não são editadas retroativamente. Se isso
importar, criar uma rotina que edite as mensagens do Discord quando o link for
convertido (hoje não existe).

### 6. Operação e segurança

- Sessão do portal expira: o bot avisa no log (`🔒 Afiliados ML: sessão ... expirada`)
  e passa a publicar o link original. Refazer o passo 2 quando acontecer.
- Rodar o bot em servidor sem tela é possível (a conversão é headless); o login
  inicial exige uma máquina com interface gráfica, depois copiar
  `data/perfil_ml_afiliados/`.
- Nunca commitar `.env`, `data/` nem `promocoes.db`.
- Confirmar que os termos dos programas de afiliados permitem esse tipo de
  publicação automática.

## Outras pendências do projeto (fora de afiliados)

- Magalu: o site devolve HTTP 403 ao navegador headless; o coletor retorna vazio.
- Pichau: só a 1ª página é coletada (as demais retornam 403).
- Mercado Livre: `/items/{id}` retorna 403 para o app; o coletor usa só os dados do catálogo.
- Botões e DMs de `/melhores` e `/alerta` ainda não foram testados em uso real no Discord.
- Descontos acima de ~60% na KaBuM!/Pichau parecem inflados (preço "de" artificial);
  avaliar baixar `DESCONTO_MAXIMO` em `collectors/common.py`.

## Entrega

1. Revisar e commitar a camada de afiliados (sem segredos).
2. Enviar para a branch do PR #3 (ou abrir PR novo) e pedir revisão.
