"""
data_layer.py
--------------
Esta é a ÚNICA parte do sistema que sabe onde os dados estão guardados.
Hoje ela fala com o Google Sheets. No futuro, se você migrar para o
Supabase, só precisa reescrever o CONTEÚDO destas funções -- o resto do
app (app.py) não muda uma linha, porque ele só conhece essas funções.

Schema v1: 17 colunas (13 originais + canal_aquisicao, tamanho_equipe,
data_entrega_combinada, nome_evento).
"""

import streamlit as st
import pandas as pd
import gspread
from streamlit_gsheets import GSheetsConnection

COLUNAS = [
    "nome_projeto",
    "data_execucao",
    "nicho_mercado",
    "tipo_cliente",
    "nome_cliente",
    "nome_evento",
    "canal_aquisicao",
    "servicos_entregues",
    "especificidade",
    "horas_captacao",
    "horas_edicao",
    "tamanho_equipe",
    "cache_total",
    "custos_operacao",
    "status_pagamento",
    "previsao_recebimento",
    "data_entrega_combinada",
]

COLUNAS_NUMERICAS = [
    "horas_captacao",
    "horas_edicao",
    "tamanho_equipe",
    "cache_total",
    "custos_operacao",
]


def _conectar():
    """Abre a conexão com a planilha configurada em .streamlit/secrets.toml"""
    return st.connection("gsheets", type=GSheetsConnection)


def _abrir_planilha_gspread():
    """
    Abre a planilha usando gspread diretamente (mesmas credenciais do secrets.toml).
    Usado só para inserir linhas novas, sem precisar reler a planilha inteira
    como o conn.update() da streamlit-gsheets-connection exige.
    """
    creds = st.secrets["connections"]["gsheets"]
    creds_dict = {
        "type": creds["type"],
        "project_id": creds["project_id"],
        "private_key_id": creds["private_key_id"],
        "private_key": creds["private_key"],
        "client_email": creds["client_email"],
        "client_id": creds["client_id"],
        "auth_uri": creds["auth_uri"],
        "token_uri": creds["token_uri"],
        "auth_provider_x509_cert_url": creds["auth_provider_x509_cert_url"],
        "client_x509_cert_url": creds["client_x509_cert_url"],
    }
    client = gspread.service_account_from_dict(creds_dict)
    return client.open_by_url(creds["spreadsheet"])


def _adicionar_linha(worksheet_nome: str, colunas: list, dados: dict):
    """
    Adiciona UMA linha no final da aba indicada, sem reler a planilha inteira.
    Mais rápido e sem o risco de duas escritas quase simultâneas se atropelarem
    (o que acontecia no padrão anterior de ler tudo -> reescrever tudo).
    """
    planilha = _abrir_planilha_gspread()
    aba = planilha.worksheet(worksheet_nome)
    linha = [dados.get(col) if dados.get(col) is not None else "" for col in colunas]
    aba.append_row(linha, value_input_option="USER_ENTERED")
    st.cache_data.clear()


def salvar_registro(registro: dict):
    """
    Recebe um dicionário com as chaves de COLUNAS e adiciona
    uma nova linha na planilha, sem reler o que já existe.
    """
    _adicionar_linha("registros", COLUNAS, registro)


def buscar_todos_registros() -> pd.DataFrame:
    """
    Retorna todos os registros já salvos, prontos para os dashboards.
    """
    conn = _conectar()
    df = conn.read(worksheet="registros", ttl=5)
    df = df.dropna(how="all")

    # Garante que colunas numéricas venham como número mesmo se o Sheets
    # devolver como texto
    for col in COLUNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def buscar_nichos_existentes() -> list:
    """
    Retorna a lista de nichos de mercado que já foram usados em algum
    registro salvo, para alimentar o dropdown do formulário.
    Nunca quebra o app: se der erro ou não houver dados, retorna lista vazia.
    """
    try:
        df = buscar_todos_registros()
        if df.empty or "nicho_mercado" not in df.columns:
            return []
        nichos = df["nicho_mercado"].dropna().astype(str).str.strip()
        nichos = nichos[nichos != ""]
        return sorted(nichos.unique().tolist())
    except Exception:
        return []


# ------------------------------------------------------------------
# PIPELINE: artistas/clientes em negociação, separado dos registros
# de trabalhos já executados. Fica numa aba própria da planilha
# chamada "pipeline".
# ------------------------------------------------------------------

PIPELINE_COLUNAS = [
    "nome_contato",
    "nicho_mercado",
    "status",
    "valor_estimado",
    "data_prevista",
    "observacoes",
]


def buscar_pipeline() -> pd.DataFrame:
    """Retorna todos os itens do pipeline (artistas/clientes em negociação)."""
    conn = _conectar()
    df = conn.read(worksheet="pipeline", ttl=5)
    df = df.dropna(how="all")
    if "valor_estimado" in df.columns:
        df["valor_estimado"] = pd.to_numeric(df["valor_estimado"], errors="coerce")
    return df


def salvar_pipeline_item(item: dict):
    """Adiciona um novo item (artista/cliente) ao pipeline, sem reler tudo."""
    _adicionar_linha("pipeline", PIPELINE_COLUNAS, item)


def atualizar_pipeline_completo(df: pd.DataFrame):
    """
    Sobrescreve a aba pipeline inteira com o dataframe editado.
    Usado depois que o usuário edita a tabela direto na tela (st.data_editor).
    """
    conn = _conectar()
    conn.update(worksheet="pipeline", data=df)
    st.cache_data.clear()
