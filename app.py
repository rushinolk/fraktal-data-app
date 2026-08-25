"""
app.py
------
Ponto de entrada do Data App. Só orquestra as abas, chamando cada módulo
de UI por responsabilidade (separação entre quem PRODUZ dado e quem
CONSOME/exibe dado):

- ui.formulario_registro -> PRODUTOR puro (registra um trabalho executado)
- ui.pipeline             -> PRODUTOR + CONSUMIDOR (adiciona e edita negociações em aberto)
- ui.dashboard            -> CONSUMIDOR puro (só lê e exibe métricas/gráficos)

Nenhum desses módulos sabe onde os dados ficam guardados -- isso é
responsabilidade exclusiva do data_layer.py.
"""

import streamlit as st

from ui import formulario_registro, pipeline, dashboard

st.set_page_config(page_title="Data App - Controle de Serviços", layout="wide")

aba_formulario, aba_pipeline, aba_dashboard = st.tabs(
    ["📝 Novo Registro", "🎯 Projetos em Aberto", "📊 Dashboards"]
)

with aba_formulario:
    formulario_registro.render()

with aba_pipeline:
    pipeline.render()

with aba_dashboard:
    dashboard.render()
