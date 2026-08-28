"""
ui/helpers.py
--------------
Funções e constantes pequenas, compartilhadas entre os módulos de UI.

A partir da v4 (schema normalizado, sem gráficos no Streamlit), este
arquivo perdeu as funções de gráfico Altair e o explodir_multivalor
(não fazem mais sentido: os catálogos agora vêm de tabelas de verdade
via data_layer, e a análise/gráfico virou responsabilidade de fora do
Streamlit). Ficou só o que ainda é usado: formatação de moeda e data.
"""

import pandas as pd


def formatar_reais(valor: float) -> str:
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    if valor is None or pd.isna(valor):
        valor = 0.0
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return f"R$ {texto}"


def formatar_data_br(valor) -> str:
    """
    Formata uma data (string ISO 'YYYY-MM-DD', date ou Timestamp) como
    'DD/MM/AAAA' -- só na exibição, o dado continua guardado em ISO no
    banco (não mexe na estrutura, só na hora de mostrar).
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    data = pd.to_datetime(valor, errors="coerce")
    if pd.isna(data):
        return str(valor)
    return data.strftime("%d/%m/%Y")


def formatar_colunas_data(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    """Aplica formatar_data_br em várias colunas de um DataFrame de exibição."""
    df = df.copy()
    for col in colunas:
        if col in df.columns:
            df[col] = df[col].apply(formatar_data_br)
    return df
