# Data App - Controle de Serviços (Fotografia/Vídeo)

## Estrutura do projeto

```
data_app/
├── app.py                   # Orquestrador fino: só monta as abas e chama os módulos de ui/
├── data_layer.py             # Única camada que sabe onde os dados ficam salvos
├── niches_config.py          # Tabela: nicho de mercado -> perguntas extras
├── opcoes.py                 # Listas de opções gerais (canais de aquisição, status do pipeline)
├── ui/
│   ├── helpers.py             # Constantes e funções pequenas compartilhadas entre os módulos
│   ├── formulario_registro.py # PRODUTOR: formulário de novo registro de trabalho executado
│   ├── pipeline.py             # PRODUTOR + CONSUMIDOR: negociações em aberto (add + edita)
│   └── dashboard.py            # CONSUMIDOR puro: métricas e gráficos
├── requirements.txt
└── .streamlit/
    └── secrets.toml           # Credenciais (você cria este arquivo, não vai pro GitHub)
```

### Por que separar assim (produtor vs consumidor)

- **`ui/formulario_registro.py`** só escreve dados (chama `salvar_registro`). Nunca lê a planilha inteira pra gerar gráfico nenhum.
- **`ui/dashboard.py`** só lê dados (chama `buscar_todos_registros`) e exibe. Nunca escreve nada.
- **`ui/pipeline.py`** é o único módulo híbrido de propósito — ele precisa ler (mostrar os itens já cadastrados) e escrever (adicionar novo item, editar status) porque essa é a natureza de um pipeline de negociação: acompanhar mudanças de status ao longo do tempo.

Essa separação deixa claro, só olhando o nome do arquivo, quem manipula o quê — e facilita muito se um dia você quiser adicionar cache mais agressivo só no lado que lê (dashboard), sem afetar o lado que escreve (formulário), por exemplo.

## Schema de dados (v1) — 16 colunas

| # | Coluna | Bloco | Descrição |
|---|---|---|---|
| 1 | `nome_projeto` | Identificação | Nome do evento/trabalho |
| 2 | `data_execucao` | Identificação | Dia da captação |
| 3 | `nicho_mercado` | Inteligência Comercial | Música Eletrônica, Imobiliário, ou qualquer outro digitado |
| 4 | `tipo_cliente` | Inteligência Comercial | Depende do nicho (ex: Produtora, Corretor) |
| 5 | `nome_cliente` | Inteligência Comercial | Quem contratou |
| 6 | `canal_aquisicao` | Inteligência Comercial | Como esse cliente chegou até ele |
| 7 | `servicos_entregues` | Inteligência Comercial | Aftermovie, Fotos, Drone, Reels |
| 8 | `especificidade` | Inteligência Comercial | Vertente musical, tipo de imóvel, etc. |
| 9 | `horas_captacao` | Esforço e Tempo | Tempo de gravação presencial |
| 10 | `horas_edicao` | Esforço e Tempo | Tempo de pós-produção |
| 11 | `tamanho_equipe` | Esforço e Tempo | Quantas pessoas trabalharam nesse job |
| 12 | `cache_total` | Controle de Caixa | Valor bruto do contrato |
| 13 | `custos_operacao` | Controle de Caixa | Gastos diretos (Uber, gasolina, assistente...) |
| 14 | `status_pagamento` | Controle de Caixa | Pendente / 50% Pago / Totalmente Pago |
| 15 | `previsao_recebimento` | Controle de Caixa | Data combinada pro dinheiro cair |
| 16 | `data_entrega_combinada` | Controle de Caixa | Prazo prometido pra entrega do material final |

## Passo a passo para configurar o Google Sheets

### 1. Criar a planilha
Crie uma planilha no Google Sheets chamada, por exemplo, `data_app_registros`.
Dentro dela, crie **duas abas (worksheets)**:

**Aba `registros`** — com esta linha de cabeçalho (copie e cole na primeira linha, célula A1):

```
nome_projeto	data_execucao	nicho_mercado	tipo_cliente	nome_cliente	nome_evento	canal_aquisicao	servicos_entregues	especificidade	horas_captacao	horas_edicao	tamanho_equipe	cache_total	custos_operacao	status_pagamento	previsao_recebimento	data_entrega_combinada
```

**Aba `pipeline`** — com esta linha de cabeçalho:

```
nome_contato	nicho_mercado	status	valor_estimado	data_prevista	observacoes
```

### 2. Criar uma conta de serviço no Google Cloud
1. Acesse https://console.cloud.google.com/ e crie um projeto novo (ou use um existente).
2. Ative as APIs **Google Sheets API** e **Google Drive API**.
3. Vá em "Credenciais" → "Criar credenciais" → "Conta de serviço".
4. Após criar, gere uma **chave JSON** para essa conta de serviço e baixe o arquivo.
5. Abra a planilha criada no passo 1 → clique em "Compartilhar" → cole o e-mail da conta de serviço (algo como `nome@projeto.iam.gserviceaccount.com`) e dê permissão de **Editor**.

### 3. Configurar o `secrets.toml`
Dentro da pasta do projeto, crie o arquivo `.streamlit/secrets.toml` com este conteúdo (preenchendo com os dados do JSON baixado):

```toml
[connections.gsheets]
spreadsheet = "URL_DA_SUA_PLANILHA_AQUI"
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

⚠️ **Nunca suba esse arquivo pro GitHub.** Se for hospedar no Streamlit Community Cloud, cole o mesmo conteúdo em "Settings" → "Secrets" do app, direto no painel deles (não precisa do arquivo local nesse caso).

### 4. Rodar localmente
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Colocando no ar para seu amigo usar pelo celular (Streamlit Community Cloud)

Como ele não mexe com código, o app precisa ficar hospedado num link que ele só abre no navegador do celular. O caminho mais simples e gratuito é o Streamlit Community Cloud.

### 1. Subir o código pro GitHub
Crie um repositório (pode ser privado) e suba todos os arquivos deste projeto:
`app.py`, `data_layer.py`, `niches_config.py`, `opcoes.py`, `requirements.txt`, `README.md`.

⚠️ **Não suba a pasta `.streamlit/secrets.toml`** — ela não deve ir pro GitHub de jeito nenhum (se você usa Git, vale adicionar `.streamlit/secrets.toml` num arquivo `.gitignore`).

### 2. Criar o app no Streamlit Community Cloud
1. Acesse https://share.streamlit.io/ e faça login com sua conta GitHub.
2. Clique em "New app" (ou "Create app").
3. Selecione o repositório, a branch (geralmente `main`), e aponte o arquivo principal: `app.py`.
4. Clique em "Deploy".

### 3. Configurar os Secrets direto no painel (sem precisar do arquivo local)
1. Com o app criado, vá em **"Settings" → "Secrets"** (dentro do painel do próprio app no Streamlit Cloud).
2. Cole exatamente o mesmo conteúdo TOML que está descrito no passo 3 da seção acima (a parte do `[connections.gsheets]`), usando os dados do JSON da conta de serviço.
3. Salve. O app reinicia sozinho e já passa a enxergar a planilha.

### 4. Gerar o link e colocar como "atalho" no celular do seu amigo
Depois do deploy, o Streamlit te dá uma URL parecida com `https://seuapp.streamlit.app`. Envie esse link pra ele e ensine a:
- **No Android (Chrome)**: abrir o link → menu (⋮) → "Adicionar à tela inicial".
- **No iPhone (Safari)**: abrir o link → botão de compartilhar (□↑) → "Adicionar à Tela de Início".

Isso cria um ícone que abre o app parecendo um aplicativo de verdade, sem barra de navegador aparecendo.

### Dica extra
Toda vez que você alterar o código no GitHub, o Streamlit Community Cloud atualiza o app sozinho em produção — você não precisa refazer o deploy manualmente.

## Aba "Projetos em Aberto" (Pipeline)

Separada dos registros de trabalhos já executados, essa aba serve pra mapear artistas/clientes
que ele está de olho ou negociando, antes de virar um contrato fechado:

- Formulário simples pra adicionar um novo item (nome, nicho, status, valor estimado, data prevista, observações).
- Tabela editável (estilo planilha): clica na célula, muda o status (Mapeado → Em Conversa → Proposta Enviada → Fechado/Perdido), salva.
- Fica numa aba própria da planilha (`pipeline`), sem misturar com os trabalhos já fechados/executados.

**Ideia pra v2**: quando um item do pipeline vira "Fechado", oferecer um botão pra converter automaticamente
num registro na aba `registros`, evitando digitar os dados do cliente duas vezes.

## Como os dados são salvos (append, não reescrita completa)

`salvar_registro()` e `salvar_pipeline_item()` usam a biblioteca `gspread` diretamente
para **adicionar uma linha nova no final da planilha**, sem reler e reescrever tudo que já existe.
Isso é mais rápido e evita o risco (pequeno, mas real) de duas escritas quase simultâneas
se atropelarem e perderem dados uma da outra.

A única operação que ainda reescreve uma aba inteira é `atualizar_pipeline_completo()`,
usada propositalmente quando o usuário edita a tabela de pipeline direto na tela
(`st.data_editor`) — nesse caso, reescrever tudo é o comportamento esperado, porque
o usuário pode ter editado várias linhas de uma vez.

## Como funciona a lógica condicional

- **Nicho de Mercado**: o dropdown mistura os nichos padrão (`niches_config.NICHOS_PADRAO`) + todos os que já apareceram em registros salvos + uma opção para digitar um nicho totalmente novo. Nunca trava o usuário numa lista fixa.
- **Perguntas extras (Tipo de Cliente / Especificidade)**: só aparecem se o nicho escolhido tiver uma entrada em `niches_config.py`. Se for um nicho novo sem configuração, o formulário segue direto para os campos padrão, sem exigir nada extra.
- **Adicionar perguntas específicas a um nicho novo no futuro**: edite apenas `niches_config.py`, adicionando uma nova entrada no dicionário `NICHOS_CONFIG`. Não é preciso tocar em `app.py`.
- **Canal de Aquisição**: segue o mesmo padrão — lista fixa em `opcoes.py` + opção de digitar algo novo.

## Dashboards incluídos na v1

1. **Rentabilidade Real por Hora** — `(cachê - custos) / horas totais`
2. **Lucro por Hora considerando o tamanho da equipe** — mesma conta, mas dividida também pelo número de pessoas envolvidas (mais justo em jobs com assistente)
3. **Previsibilidade de Caixa** — quanto dinheiro deve entrar, agrupado por data de previsão de recebimento
4. **Painel de Cobrança** — lista de quem ainda não pagou 100%
5. **Mapa de Calor do Mercado** — ticket médio por especificidade (vertente musical, tipo de imóvel, etc.)
6. **Canal de Aquisição mais lucrativo** — ticket médio por canal, para saber onde focar esforço de prospecção
7. **Prazos de Entrega Mais Próximos** — tabela ordenada pelas entregas mais urgentes

## Caminho de migração futura (Google Sheets → Supabase)

Quando o volume de dados ou a complexidade dos relatórios justificar, a migração
exige mexer **apenas** em `data_layer.py`:

- `salvar_registro()` passa a fazer um `INSERT` numa tabela SQL em vez de escrever na planilha.
- `buscar_todos_registros()` passa a fazer um `SELECT * FROM registros` em vez de ler a planilha.
- `buscar_nichos_existentes()` passa a fazer um `SELECT DISTINCT nicho_mercado FROM registros`.

O `app.py`, o `niches_config.py` e o `opcoes.py` permanecem exatamente iguais,
porque nenhum deles conversa diretamente com a fonte de dados — só com as funções do `data_layer.py`.

## Ideias para uma v2 (não implementadas ainda, para não sobrecarregar o formulário agora)

- Capturar a **data real de entrega** (não só a combinada) para medir taxa de atraso de verdade.
- Normalizar nichos/canais digitados como "Outro" para evitar duplicidade por diferença de digitação (ex: "Casamento" vs "Casamentos").
- Contagem de clientes recorrentes (já é possível hoje analisando `nome_cliente` repetido, sem precisar de campo novo).
