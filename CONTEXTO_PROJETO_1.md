# Contexto do Projeto — Data App Fraktal

> Documento de referência para retomar o projeto a qualquer momento sem perder o fio da meada.
> Última atualização: sessão de redesenho do banco (v3 → v4, OLTP normalizado).

---

## 1. Objetivo do projeto

Construir uma experiência de dados completa — não um projeto simples pra um amigo, mas algo
com padrão de mercado, tanto pro amigo freelancer de fotografia/vídeo (marca **Fraktal**,
atendendo Música Eletrônica e Mercado Imobiliário) quanto pro Arthur, que constrói, mantém e atua
como consultor/analista de dados dele.

O amigo é **PC-comfortable mas não-técnico** e só interage com o app pronto — nunca vê banco,
tabela ou gráfico de análise bruto. Ele usa o Streamlit só pra cadastrar trabalhos, acompanhar o
pipeline de negociação, e ver o financeiro operacional (quem deve pagar, o que falta entregar).

**Análise de mercado e apresentação elaborada não ficam no Streamlit** — essa camada é
responsabilidade separada do Arthur, usando os dados do OLTP como fonte (ver seção 9).

---

## 2. Arquitetura atual (v4 — OLTP normalizado)

| Decisão | Motivo |
|---|---|
| Supabase (Postgres) como banco | Ver histórico de migração na seção 8. |
| **Schema totalmente normalizado** (v4) | O schema anterior (v2/v3) era essencialmente "planilha dentro de banco relacional": uma tabela larga (`registros`) com colunas multivaloradas guardadas como texto separado por vírgula (violava 1FN), sem entidade `cliente` de verdade, sem integridade referencial nos catálogos. Decisão do Arthur, motivada por visão de longo prazo pro projeto (não só a necessidade imediata do volume atual). Como nenhum dado real de produção existia ainda, foi possível fazer um corte limpo (drop + recreate) sem migração de dado. |
| **Catálogos geridos pelo Arthur, não pelo usuário final** | Nicho, tipo de cliente, canal de aquisição, serviço, especificidade, pessoas da equipe e suas funções viraram tabelas próprias no banco (antes viviam em `niches_config.py`/`opcoes.py`, ou eram digitáveis "na hora" no formulário). O formulário agora só *lê* essas tabelas — cadastro de opção nova é feito pelo Arthur direto no Supabase quando o amigo pedir. Isso garante padronização do que é escrito e elimina duplicidade por digitação (ex: "Casamento" vs "Casamentos"). `clientes` é a exceção: cresce organicamente a cada trabalho novo (não é curado), porque é dado de negócio real, não taxonomia. |
| **`niches_config.py` foi substituído por dado no banco** | Os flags que antes viviam nesse arquivo Python (`evento_obrigatorio`, `tipos_sem_nome_no_projeto`, tipo de especificidade) agora são colunas nas tabelas `nichos` e `tipos_cliente`. Isso é uma mudança de padrão real em relação à decisão anterior ("niches_config.py é a única tabela editável") — motivada pela própria decisão do Arthur de normalizar o OLTP, não uma reversão não solicitada. |
| **Gravação atômica via função no Postgres (`registrar_trabalho`)** | Como salvar 1 trabalho agora envolve várias tabelas (cliente + trabalho + bridges de serviço/especificidade/equipe), a lógica de "tudo ou nada" foi movida pro banco (PL/pgSQL, chamada via `.rpc()`), em vez de o Streamlit fazer 4-5 inserts soltos e arriscar gravação parcial. |
| **Benefícios da equipe como colunas booleanas** (não array, não tabela-ponte extra) | `recebeu_transporte`/`recebeu_alimentacao`/`recebeu_consumacao`/`recebeu_ingresso` direto em `trabalho_equipe`. Decisão consciente: array de texto foi descartado (o Arthur não gostou, mesmo problema de "documento dentro de coluna" que motivou a normalização toda), e uma tabela-ponte extra foi considerada over-engineering pra um conjunto pequeno e estável de flags. `valor_estimado_beneficio` fica reservado (não usado) caso decida monetizar isso no futuro. |
| **Gráficos saíram do Streamlit** | Tudo que é análise/visualização de mercado (rentabilidade por hora, mapa de calor, canal mais lucrativo) deixou de existir no app — o Arthur vai construir essa camada separadamente (ver seção 9). Ficou só o operacional: cards de resumo, painel de cobrança, prazos de entrega, previsibilidade de caixa (agora como tabela, não gráfico). |
| **Horas de Captação/Edição removidas** | O amigo não conseguia estimar esses campos de forma confiável — dado chutado é pior que não ter dado. Foram substituídos pela seção "Equipe envolvida": quem participou, em que função, cachê pago e benefícios recebidos por pessoa. |
| **Datas exibidas em dd/mm/aaaa** | Só na camada de exibição (`ui/helpers.formatar_data_br`), sem alterar como a data é armazenada (continua `date` no Postgres, ISO por baixo). |

**Prova de que o isolamento em `data_layer.py` funcionou**: mesmo essa reestruturação profunda do
schema não exigiu tocar em `app.py` além de remover a aba de dashboards — o resto do app continuou
falando só com as funções de `data_layer.py`.

---

## 3. Schema de dados (Supabase — v4, normalizado)

**Catálogos (Arthur mantém, direto no Supabase):**

| Tabela | Campos principais |
|---|---|
| `nichos` | id, nome, `evento_obrigatorio`, `especificidade_label`, `especificidade_multipla` |
| `tipos_cliente` | id, nicho_id (FK), nome, `incluir_no_nome_projeto` |
| `canais_aquisicao` | id, nome |
| `servicos` | id, nome |
| `especificidades` | id, nicho_id (FK), nome |
| `pessoas_equipe` | id, nome |
| `funcoes_equipe` | id, nome |

**Entidades principais:**

| Tabela | Campos principais |
|---|---|
| `clientes` | id, nome (cresce organicamente via `registrar_trabalho`, não é catálogo curado) |
| `trabalhos` | id, cliente_id, nicho_id, tipo_cliente_id, canal_aquisicao_id, nome_projeto, nome_evento, data_execucao, moeda, taxa_cambio, cache_total, custos_operacao, status_pagamento, previsao_recebimento, data_entrega_combinada |
| `trabalho_servicos` | trabalho_id + servico_id (bridge N:N) |
| `trabalho_especificidades` | trabalho_id + especificidade_id (bridge N:N) |
| `trabalho_equipe` | id, trabalho_id, pessoa_id, funcao_id, cache_pago, recebeu_transporte, recebeu_alimentacao, recebeu_consumacao, recebeu_ingresso, valor_estimado_beneficio (reservado) |
| `pipeline` | id, nome_contato, nicho_id (FK), status, valor_estimado, data_prevista, observacoes |

**Função de gravação**: `registrar_trabalho(payload jsonb)` — acha-ou-cria o cliente, insere o
trabalho e os vínculos de serviço/especificidade/equipe numa transação só. Chamada via `.rpc()`
do `supabase-py`.

Diagrama ER completo foi gerado e mostrado durante a sessão de design (ver histórico da conversa).

---

## 4. Estrutura de arquivos atual

```
fraktal_registros/
├── app.py                     # Orquestrador fino: 3 abas (sem Dashboards)
├── data_layer.py               # Única camada que sabe onde os dados ficam (Supabase, schema v4)
├── opcoes.py                    # Só os enums realmente fixos: status_pagamento, status_pipeline, moedas
├── requirements.txt              # streamlit, pandas, supabase
├── supabase_schema_v4.sql         # Schema completo (drop+recreate) + seed data + função registrar_trabalho
├── README.md
├── ui/
│   ├── __init__.py
│   ├── helpers.py                 # Formatação de moeda e data (dd/mm/aaaa) -- sem gráfico
│   ├── formulario_registro.py      # PRODUTOR puro -- catálogos vêm do banco, seção de equipe
│   ├── pipeline.py                  # PRODUTOR + CONSUMIDOR -- nicho agora é FK
│   └── financeiro.py                 # CONSUMIDOR puro -- cards, cobrança, prazos, caixa (tabela)
└── .streamlit/
    └── secrets.toml               # URL + Service Role Key do Supabase

ARQUIVOS ÓRFÃOS (não usados mais, remover manualmente do repositório):
├── ui/dashboard.py                 # Análises de mercado saíram do Streamlit
├── niches_config.py                 # Substituído pelas tabelas nichos/tipos_cliente no banco
```

---

## 5. Funcionalidades já implementadas

- Cadastro de trabalho com catálogos vindos do banco (nicho, tipo de cliente, canal, serviço,
  especificidade multivalorada quando o nicho permite)
- Sugestão automática de Nome do Projeto, respeitando o flag `incluir_no_nome_projeto` por tipo
  de cliente (ex: "Produtora" não entra no nome quando há evento)
- Seção "Equipe envolvida": pessoa, função, cachê pago e benefícios recebidos (transporte,
  alimentação, consumação, ingresso), editável como mini-tabela (`st.data_editor`)
- Suporte a moeda estrangeira (USD/EUR) com taxa de câmbio manual, convertendo pra Real nos
  totais do Financeiro
- Aba de Pipeline com nicho como FK real (dropdown + edição em tabela)
- Aba Financeiro: cards de resumo, previsibilidade de caixa (tabela), painel de cobrança, prazos
  de entrega — datas exibidas em dd/mm/aaaa
- Gravação atômica de um trabalho completo (cliente + trabalho + bridges) via função no Postgres

---

## 6. Problemas já resolvidos (não repetir o mesmo troubleshooting)

- Bug do "+ Adicionar novo nicho..." sendo salvo literalmente no Pipeline — **não se aplica
  mais**: catálogos não são mais digitáveis on-the-fly, viraram select vindo do banco.
- Gráficos nativos do Streamlit (`st.bar_chart`) ficavam espichados/ilegíveis — **não se aplica
  mais**: gráficos saíram do Streamlit inteiramente nesta sessão.
- Erro de import `calcular_metricas` — função existia numa versão intermediária do `ui/helpers.py`
  que foi descontinuada; o arquivo atual não depende mais dela.

---

## 7. Pendências / Próximos passos

### Pendências técnicas
1. **Rodar `supabase_schema_v4.sql`** no SQL Editor do Supabase — dropa o schema anterior e recria
   tudo do zero (seguro, sem dado real de produção pra perder).
2. **Ajustar o seed data de `pessoas_equipe`** com os nomes reais da equipe (o script insere
   placeholders "Arthur" e "Amigo do Drone").
3. Testar o fluxo completo de novo registro (equipe, câmbio, especificidade múltipla) contra o
   banco recriado.

### Ideias de v2 (adiadas conscientemente)
- Botão pra converter um item do Pipeline em trabalho fechado.
- Capturar data real de entrega (não só a combinada).
- Decidir se `valor_estimado_beneficio` (em `trabalho_equipe`) será usado — hoje é campo
  reservado, sem UI.

### Ainda não feito
- Deploy real no Streamlit Community Cloud.
- Inserção de dado real da operação (só teste fictício até agora).

---

## 8. Histórico de migração de banco

1. **v1 — Google Sheets**: schema inicial, abandonado porque o amigo nunca precisaria abrir
   planilha e o gspread trazia dor de cabeça própria (quota de API, corrida de escrita).
2. **v2/v3 — Supabase, schema largo**: uma tabela `registros` com ~20 colunas, incluindo
   multivaloradas como texto (servicos_entregues, especificidade, beneficios_contratante). Deu
   certo como MVP rápido, mas o próprio Arthur identificou que era "planilha dentro de banco".
3. **v4 — Supabase, schema normalizado (atual)**: catálogos próprios, tabela fato `trabalhos`,
   tabelas-ponte pra relações N:N, gravação atômica via função no banco. Ver seção 2.

---

## 9. Camada OLAP / apresentação (fora do escopo deste app, por enquanto)

O Arthur pretende construir, separadamente, um pipeline que move dados do OLTP (Supabase) pra uma
camada OLAP e monta a apresentação/análise pro amigo — esse trabalho **não é prioridade agora**;
o foco atual é fechar e entregar uma v1 usável do OLTP + Streamlit operacional. Quando essa frente
avançar, retomar a discussão de onde o OLAP mora (mesmo Postgres via views/matviews, ou motor
separado) e como as dimensões multivaloradas (serviços, especificidades) vão virar bridge tables
do lado analítico.
