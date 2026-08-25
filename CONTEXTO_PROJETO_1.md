# Contexto do Projeto — Data App Fraktal

> Documento de referência para retomar o projeto a qualquer momento sem perder o fio da meada.
> Última atualização: sessão em que o projeto ficou pausado após a modularização em `ui/`.

---

## 1. Objetivo do projeto

Construir um Data App simples (Streamlit + Google Sheets) para substituir o controle manual/planilhas
soltas de um amigo freelancer de fotografia/vídeo (marca **Fraktal**), que atende principalmente:

- **Música Eletrônica**: aftermovies para produtoras, DJs ou pacotes fechados diretamente com o artista.
- **Mercado Imobiliário**: captação aérea (drone) e fotos para corretores/imobiliárias/construtoras.
- Potencialmente outros nichos no futuro (o app foi desenhado pra nunca travar nisso).

O amigo é **PC-comfortable mas não-técnico** — ele vai usar o app pronto, não mexer em código.
Quem constrói e mantém é o Arthur (usuário deste projeto).

**Objetivo de longo prazo**: não é só "montar gráfico bonito", é criar a fundação de coleta de dados
pra um negócio que hoje não tem maturidade de dados nenhuma (controle por memória, sem planilha).

---

## 2. Decisões de arquitetura e por quê

| Decisão | Motivo |
|---|---|
| Streamlit (Python) | Fácil de fazer formulário + dashboard no mesmo lugar, hospedagem gratuita, funciona como "app" no celular via atalho |
| Google Sheets como banco de dados (v1) | Simples de configurar, sem precisar gerenciar banco de dados; amigo consegue abrir a planilha manualmente se quiser |
| Supabase como caminho de migração futura | Só necessário se a operação virar multi-usuário ou os dados ficarem relacionalmente complexos — não é uma questão de "tempo", é de mudança de escala do negócio |
| `layout="wide"` | O amigo usa mais PC que celular, então o formulário aproveita a tela larga em vez de ficar compactado ao centro |
| Escrita via `gspread.append_row()` (não `conn.update()` sobrescrevendo tudo) | O padrão anterior de ler tudo → reescrever tudo tinha risco (baixo, mas real) de duas escritas quase simultâneas se atropelarem. Corrigido nessa sessão. |
| Módulos separados em `ui/` por responsabilidade (produtor vs consumidor) | Streamlit reexecuta o script inteiro a cada interação — separar deixa claro o que só escreve, o que só lê, e o que faz as duas coisas (pipeline) |
| `niches_config.py` isolado | Adicionar um nicho novo com perguntas específicas no futuro (ex: Casamentos) não deve exigir mexer no `app.py` |

---

## 3. Schema de dados (Google Sheets)

A planilha tem **duas abas**:

### Aba `registros` (trabalhos já executados) — 17 colunas

| Coluna | Bloco | Observação |
|---|---|---|
| `nome_projeto` | Identificação | Sugestão automática: se tiver Nome do Evento, vira `Cliente/DJ + Evento + Ano` (ex: "Dezzert Infected 2025"); senão, `Cliente - Especificidade - Data` |
| `data_execucao` | Identificação | Data da captação |
| `nicho_mercado` | Comercial | Dropdown dinâmico (padrão + já usados) + opção de digitar nicho novo |
| `tipo_cliente` | Comercial | Depende do nicho (via `niches_config.py`) |
| `nome_cliente` | Comercial | Nome do DJ/corretor/produtora/contratante |
| `nome_evento` | Comercial | Nome do evento/festa (opcional hoje — **deveria ser obrigatório pra Música Eletrônica**, ver Pendências) |
| `canal_aquisicao` | Comercial | Lista fixa (Indicação, Instagram, Evento Anterior, Prospecção Ativa, Já era Cliente) + opção de digitar outro |
| `servicos_entregues` | Comercial | Multi-select: Aftermovie, Fotos, Voo de Drone, Reels |
| `especificidade` | Comercial | Vertente musical (texto livre) ou tipo de captação imobiliária (lista fechada), depende do nicho |
| `horas_captacao` | Esforço/Tempo | Só controle interno — ele não cobra por hora |
| `horas_edicao` | Esforço/Tempo | Idem |
| `tamanho_equipe` | Esforço/Tempo | Quantas pessoas trabalharam (pra calcular lucro/hora por pessoa) |
| `cache_total` | Caixa | **Valor do Pacote Negociado** — ele cobra por pacote fechado, não por hora |
| `custos_operacao` | Caixa | Gastos diretos (Uber, gasolina, assistente...) |
| `status_pagamento` | Caixa | Pendente / 50% Pago / Totalmente Pago |
| `previsao_recebimento` | Caixa | Data combinada pro dinheiro cair |
| `data_entrega_combinada` | Caixa | Prazo prometido pra entrega do material final |

### Aba `pipeline` (negociações em aberto, separado dos trabalhos fechados) — 6 colunas

| Coluna | Observação |
|---|---|
| `nome_contato` | Nome do artista/cliente que ele está de olho |
| `nicho_mercado` | Reaproveita a mesma lista de nichos do formulário principal |
| `status` | Mapeado → Em Conversa → Proposta Enviada → Fechado / Perdido |
| `valor_estimado` | Opcional |
| `data_prevista` | Data prevista do evento, opcional |
| `observacoes` | Texto livre |

---

## 4. Estrutura de arquivos atual

```
fraktal_registros/
├── app.py                     # Orquestrador fino: monta as 3 abas e chama os módulos de ui/
├── data_layer.py               # ÚNICA camada que sabe onde os dados ficam (Google Sheets hoje)
├── niches_config.py             # Tabela: nicho -> perguntas extras (tipo_cliente, especificidade)
├── opcoes.py                    # Listas gerais: canais de aquisição, status do pipeline
├── requirements.txt              # streamlit, pandas, st-gsheets-connection, gspread
├── README.md                     # Setup completo (Google Cloud, secrets.toml, deploy, schema)
├── .gitignore                    # Protege o secrets.toml de ir pro GitHub
├── ui/
│   ├── __init__.py
│   ├── helpers.py                 # Constantes + funções pequenas compartilhadas
│   ├── formulario_registro.py      # PRODUTOR puro (formulário de novo registro)
│   ├── pipeline.py                  # PRODUTOR + CONSUMIDOR (pipeline de negociação)
│   └── dashboard.py                  # CONSUMIDOR puro (métricas e gráficos)
└── .streamlit/
    └── secrets.toml               # Credenciais da conta de serviço Google (nunca vai pro git)
```

---

## 5. Funcionalidades já implementadas

- Formulário de registro com lógica condicional por nicho (extensível sem mexer no `app.py`)
- Dropdown de nicho dinâmico (nichos já usados + opção de cadastrar nicho novo, sem travar em lista fixa)
- Sugestão automática de Nome do Projeto (Cliente/DJ + Evento + Ano)
- Canal de Aquisição com lista fixa + opção de digitar novo
- Controle de equipe (tamanho da equipe) pra calcular lucro por hora por pessoa, não só por hora total
- Aba de Pipeline: formulário simples de adicionar + tabela editável estilo planilha (`st.data_editor`) pra mudar status
- Dashboard com: cards de resumo (Faturado/Recebido/Pendente/Lucro), rentabilidade por hora, lucro por hora por pessoa, previsibilidade de caixa, painel de cobrança, mapa de calor por especificidade, canal de aquisição mais lucrativo, prazos de entrega próximos
- Escrita via `append_row` (gspread direto), evitando reler/reescrever a planilha inteira a cada save
- Deploy documentado (não feito ainda) pro Streamlit Community Cloud, com atalho na tela inicial do celular

---

## 6. Problemas já resolvidos (não repetir o mesmo troubleshooting)

- Nome errado no `requirements.txt`: o pacote pip é `st-gsheets-connection` (import continua `streamlit_gsheets`)
- `PermissionError` do gspread: faltava compartilhar a planilha com o `client_email` da conta de serviço, com permissão de Editor
- `SERVICE_DISABLED` (403): faltava ativar a **Google Sheets API** e a **Google Drive API** no projeto do Google Cloud
- `secrets.toml` vai dentro de uma pasta `.streamlit/` na raiz do projeto (não é um arquivo solto na raiz)
- Todos os arquivos do projeto (exceto `.streamlit/secrets.toml`) já foram apagados uma vez por acidente e restaurados a partir de backups fornecidos — **vale manter um `.zip` de backup externo** (já foi gerado um e entregue)

---

## 7. Pendências / Próximos passos

### Pendências técnicas (combinadas mas não implementadas ainda)
1. **Separar a aba Dashboards em duas abas**: `💰 Financeiro` (cards de resumo + previsibilidade de caixa + painel de cobrança + prazos de entrega) e `📊 Dashboards` (só análises de mercado: rentabilidade por hora, lucro por hora por pessoa, mapa de calor, canal de aquisição). Motivo: o usuário achou tudo junto "bagunçado" ao testar.
2. **Reequilibrar as colunas do formulário**: hoje `Tipo de Cliente`/`Especificidade` ficam numa linha separada abaixo das duas colunas (Nicho | Cliente+Evento+Canal), criando um vão vazio estranho debaixo do Nicho. Ajuste combinado: mover `Tipo de Cliente`/`Especificidade` pra dentro da mesma coluna do Nicho, empilhados, deixando as duas colunas com altura parecida.
3. **Nome do Evento obrigatório para Música Eletrônica**: adicionar um flag `"evento_obrigatorio": True` na entrada de "Música Eletrônica" dentro de `niches_config.py`, e usar esse flag tanto pra validação (não deixar salvar sem preencher) quanto pra indicar visualmente no rótulo do campo. Deve ser genérico o suficiente pra outros nichos usarem o mesmo flag no futuro.

### Ideias de v2 (levantadas mas conscientemente adiadas, pra não sobrecarregar o MVP agora)
- Botão pra converter um item do Pipeline em "Fechado" diretamente num registro da aba `registros`, evitando digitar os dados do cliente duas vezes.
- Capturar a **data real de entrega** (não só a combinada) pra medir taxa de atraso de verdade.
- Normalizar nichos/canais digitados como "outro" pra evitar duplicidade por diferença de digitação (ex: "Casamento" vs "Casamentos").
- Contagem de clientes recorrentes (já dá pra fazer hoje analisando `nome_cliente` repetido, sem precisar de campo novo).

### Ainda não feito (não é bug, só não chegou a acontecer)
- Deploy real no Streamlit Community Cloud (só foi testado local até agora)
- Envio do link/atalho pro amigo de fato começar a usar
- Qualquer dado real da operação dele ainda não foi inserido (os testes foram com dados fictícios)

---

## 8. Caminho de migração futura (Google Sheets → Supabase)

Só migrar o conteúdo de `data_layer.py` — nenhum outro arquivo do projeto precisa mudar, porque
`app.py`, `niches_config.py`, `opcoes.py` e os módulos de `ui/` só conversam com as funções do
`data_layer.py`, nunca diretamente com a fonte de dados.

O gatilho pra migrar não é "tempo passado", é **mudança de escala do negócio**: múltiplos usuários
simultâneos, necessidade de permissões por pessoa, ou dados relacionalmente mais complexos do que
uma tabela simples resolve.
