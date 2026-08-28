"""
app.py
------
Ponto de entrada do Data App. Só orquestra as abas, chamando cada módulo
de UI por responsabilidade:

- ui.formulario_registro -> PRODUTOR puro (registra um trabalho executado)
- ui.pipeline             -> PRODUTOR + CONSUMIDOR (negociações em aberto)
- ui.financeiro           -> CONSUMIDOR puro (caixa: resumo, previsibilidade, cobrança, prazos)

A partir da v4, a aba de Dashboards de mercado saiu do Streamlit -- passa
a ser responsabilidade da camada OLAP/apresentação que fica fora deste
app. `ui/dashboard.py` não é mais importado (arquivo órfão no repositório
até você remover manualmente).
"""

import streamlit as st

from ui import formulario_registro, pipeline, financeiro

st.set_page_config(page_title="Data App - Controle de Serviços", layout="wide")

aba_formulario, aba_pipeline, aba_financeiro = st.tabs(
    ["📝 Novo Registro", "🎯 Projetos em Aberto", "💰 Financeiro"]
)

with aba_formulario:
    formulario_registro.render()

with aba_pipeline:
    pipeline.render()

with aba_financeiro:
    financeiro.render()
