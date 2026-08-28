"""
data_layer.py
--------------
Esta é a ÚNICA parte do sistema que sabe onde os dados estão guardados.

Schema v4: OLTP normalizado. Catálogos (nichos, tipos_cliente,
canais_aquisicao, servicos, especificidades, pessoas_equipe,
funcoes_equipe) são geridos direto no Supabase -- o app só lê. A
gravação de um trabalho (cliente + trabalho + serviços/especificidades +
equipe) é feita numa chamada só à função registrar_trabalho() do banco
(via RPC), que cuida de tudo dentro de uma transação -- assim o Streamlit
não precisa fazer 4-5 inserts soltos e torcer pra nenhum falhar no meio.
"""

import streamlit as st
import pandas as pd
from supabase import create_client, Client


@st.cache_resource
def _conectar() -> Client:
    """Abre (e reaproveita) a conexão com o projeto Supabase."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ------------------------------------------------------------------
# CATÁLOGOS -- só leitura. Cacheados por mais tempo (ttl maior) porque
# mudam raramente (só quando você adiciona algo novo direto no Supabase).
# ------------------------------------------------------------------

@st.cache_data(ttl=60)
def buscar_nichos() -> list[dict]:
    """Cada nicho já traz os flags de comportamento (evento obrigatório,
    rótulo e tipo da especificidade) -- isso substitui o antigo
    niches_config.py: agora é dado no banco, não código."""
    client = _conectar()
    resposta = client.table("nichos").select("*").order("nome").execute()
    return resposta.data or []


@st.cache_data(ttl=60)
def buscar_tipos_cliente(nicho_id: int) -> list[dict]:
    client = _conectar()
    resposta = (
        client.table("tipos_cliente")
        .select("*")
        .eq("nicho_id", nicho_id)
        .order("nome")
        .execute()
    )
    return resposta.data or []


@st.cache_data(ttl=60)
def buscar_canais_aquisicao() -> list[dict]:
    client = _conectar()
    resposta = client.table("canais_aquisicao").select("*").order("nome").execute()
    return resposta.data or []


@st.cache_data(ttl=60)
def buscar_servicos() -> list[dict]:
    client = _conectar()
    resposta = client.table("servicos").select("*").order("nome").execute()
    return resposta.data or []


@st.cache_data(ttl=60)
def buscar_especificidades(nicho_id: int) -> list[dict]:
    client = _conectar()
    resposta = (
        client.table("especificidades")
        .select("*")
        .eq("nicho_id", nicho_id)
        .order("nome")
        .execute()
    )
    return resposta.data or []


@st.cache_data(ttl=60)
def buscar_pessoas_equipe() -> list[dict]:
    client = _conectar()
    resposta = client.table("pessoas_equipe").select("*").order("nome").execute()
    return resposta.data or []


@st.cache_data(ttl=60)
def buscar_funcoes_equipe() -> list[dict]:
    client = _conectar()
    resposta = client.table("funcoes_equipe").select("*").order("nome").execute()
    return resposta.data or []


# ------------------------------------------------------------------
# TRABALHOS -- gravação via RPC (atômica) + leitura pro Financeiro.
# ------------------------------------------------------------------

def registrar_trabalho(payload: dict):
    """
    Chama a função registrar_trabalho() no Postgres via RPC: acha-ou-cria
    o cliente, insere o trabalho, e insere os vínculos de serviços,
    especificidades e equipe -- tudo numa transação só do lado do banco.
    """
    client = _conectar()
    client.rpc("registrar_trabalho", {"payload": payload}).execute()
    st.cache_data.clear()


@st.cache_data(ttl=5)
def buscar_trabalhos() -> pd.DataFrame:
    """
    Retorna os trabalhos com o nome do cliente já embutido (join via
    PostgREST), prontos pro Financeiro. Não inclui serviços/especificidade/
    equipe -- esta tela é operacional (cobrança, prazos), não analítica.
    """
    client = _conectar()
    resposta = (
        client.table("trabalhos")
        .select("*, clientes(nome)")
        .order("id")
        .execute()
    )
    dados = resposta.data or []

    if not dados:
        return pd.DataFrame(
            columns=[
                "id", "nome_cliente", "nome_projeto", "nome_evento",
                "data_execucao", "moeda", "taxa_cambio", "cache_total",
                "custos_operacao", "status_pagamento", "previsao_recebimento",
                "data_entrega_combinada",
            ]
        )

    df = pd.DataFrame(dados)
    df["nome_cliente"] = df["clientes"].apply(lambda c: c.get("nome") if isinstance(c, dict) else None)
    df = df.drop(columns=["clientes"])

    for col in ["taxa_cambio", "cache_total", "custos_operacao"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ------------------------------------------------------------------
# PIPELINE: mesma lógica de antes, só troca nicho texto por nicho_id (FK).
# ------------------------------------------------------------------

PIPELINE_COLUNAS = ["nome_contato", "nicho_id", "status", "valor_estimado", "data_prevista", "observacoes"]


@st.cache_data(ttl=5)
def buscar_pipeline() -> pd.DataFrame:
    """Retorna o pipeline com o nome do nicho já embutido (join), pra exibir na tabela."""
    client = _conectar()
    resposta = client.table("pipeline").select("*, nichos(nome)").order("id").execute()
    dados = resposta.data or []

    if not dados:
        return pd.DataFrame(
            columns=["nome_contato", "nicho_mercado", "status", "valor_estimado", "data_prevista", "observacoes"]
        )

    df = pd.DataFrame(dados)
    df["nicho_mercado"] = df["nichos"].apply(lambda n: n.get("nome") if isinstance(n, dict) else None)
    df = df.drop(columns=["nichos", "id", "nicho_id", "created_at"], errors="ignore")
    df["valor_estimado"] = pd.to_numeric(df["valor_estimado"], errors="coerce")
    # Vem como string ISO do Supabase -- precisa ser datetime de verdade
    # pra st.column_config.DateColumn aceitar editar a coluna.
    df["data_prevista"] = pd.to_datetime(df["data_prevista"], errors="coerce")

    ordem = ["nome_contato", "nicho_mercado", "status", "valor_estimado", "data_prevista", "observacoes"]
    return df[[c for c in ordem if c in df.columns]]


@st.cache_data(ttl=5)
def buscar_pipeline_convertivel() -> list[dict]:
    """
    Itens do pipeline ainda não fechados, usados pra popular o conversor
    "Pipeline -> Trabalho" na aba de Projetos em Aberto.
    """
    client = _conectar()
    resposta = (
        client.table("pipeline")
        .select("id, nome_contato, nicho_id, valor_estimado, nichos(nome)")
        .neq("status", "Fechado")
        .order("id")
        .execute()
    )
    dados = resposta.data or []
    itens = []
    for d in dados:
        nicho = d.get("nichos") or {}
        itens.append({
            "id": d["id"],
            "nome_contato": d["nome_contato"],
            "nicho_id": d["nicho_id"],
            "nicho_nome": nicho.get("nome"),
            "valor_estimado": d.get("valor_estimado"),
        })
    return itens


def marcar_pipeline_fechado(pipeline_id: int):
    """Marca um item do pipeline como Fechado -- usado quando ele vira um trabalho de verdade."""
    client = _conectar()
    client.table("pipeline").update({"status": "Fechado"}).eq("id", pipeline_id).execute()
    st.cache_data.clear()


def salvar_pipeline_item(item: dict):
    """Adiciona um novo item ao pipeline. Espera `nicho_id`, não nome do nicho."""
    client = _conectar()
    linha = {col: item.get(col) for col in PIPELINE_COLUNAS}
    client.table("pipeline").insert(linha).execute()
    st.cache_data.clear()


def atualizar_pipeline_completo(df: pd.DataFrame):
    """
    Sobrescreve a tabela pipeline inteira com o dataframe editado.
    Espera uma coluna `nicho_id` já resolvida pelo chamador (ui/pipeline.py
    faz o mapeamento nome -> id antes de chamar esta função).
    """
    client = _conectar()
    df_colunas_negocio = df[PIPELINE_COLUNAS].copy()

    # Volta de datetime (usado pelo DateColumn na tela) pra string ISO
    # (ou None se vazio) -- o Supabase espera texto/data, não Timestamp.
    if "data_prevista" in df_colunas_negocio.columns:
        df_colunas_negocio["data_prevista"] = pd.to_datetime(
            df_colunas_negocio["data_prevista"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    df_limpo = df_colunas_negocio.where(pd.notnull(df_colunas_negocio), None)
    registros = df_limpo.to_dict("records")

    client.table("pipeline").delete().neq("id", -1).execute()
    if registros:
        client.table("pipeline").insert(registros).execute()

    st.cache_data.clear()
