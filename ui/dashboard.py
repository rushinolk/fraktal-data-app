"""
ui/dashboard.py
----------------
Módulo CONSUMIDOR puro: só lê os dados (via data_layer.buscar_todos_registros)
e exibe métricas/gráficos. Nunca escreve nada na planilha -- essa
responsabilidade é do ui/formulario_registro.py e do ui/pipeline.py.
"""

import pandas as pd
import streamlit as st

from data_layer import buscar_todos_registros
from ui.helpers import formatar_reais


def render():
    st.header("Inteligência do Negócio")

    df = buscar_todos_registros()

    if df.empty:
        st.info("Ainda não há registros. Adicione o primeiro na aba 'Novo Registro'.")
        return

    df["horas_totais"] = df["horas_captacao"] + df["horas_edicao"]
    df["lucro"] = df["cache_total"] - df["custos_operacao"]
    df["lucro_por_hora"] = df["lucro"] / df["horas_totais"].replace(0, pd.NA)
    df["lucro_por_hora_por_pessoa"] = df["lucro_por_hora"] / df["tamanho_equipe"].replace(0, pd.NA)

    # Resumo rápido no topo -- pensado para quem não quer interpretar
    # gráfico nenhum, só ver o número e entender na hora.
    total_faturado = df["cache_total"].sum()
    total_recebido = df.loc[df["status_pagamento"] == "Totalmente Pago", "cache_total"].sum()
    total_pendente = total_faturado - total_recebido
    lucro_total = df["lucro"].sum()

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("💰 Total Faturado", formatar_reais(total_faturado))
    col_b.metric("✅ Já Recebido", formatar_reais(total_recebido))
    col_c.metric("⏳ Pendente de Receber", formatar_reais(total_pendente))
    col_d.metric("📈 Lucro Total", formatar_reais(lucro_total))

    st.divider()

    st.subheader("💰 Rentabilidade Real por Hora")
    st.bar_chart(df.set_index("nome_projeto")["lucro_por_hora"])

    st.subheader("👥 Lucro por Hora, considerando o tamanho da equipe")
    st.caption("Mais justo que o gráfico acima quando ele leva assistentes — divide o lucro/hora pelas pessoas envolvidas.")
    st.bar_chart(df.set_index("nome_projeto")["lucro_por_hora_por_pessoa"])

    st.subheader("📅 Previsibilidade de Caixa")
    pendentes = df[df["status_pagamento"] != "Totalmente Pago"]
    if not pendentes.empty:
        caixa_futuro = pendentes.groupby("previsao_recebimento")["cache_total"].sum()
        st.line_chart(caixa_futuro)
    else:
        st.write("Nenhum recebimento pendente no momento.")

    st.subheader("📋 Painel de Cobrança")
    if not pendentes.empty:
        st.dataframe(
            pendentes[["nome_cliente", "nome_projeto", "cache_total", "status_pagamento", "previsao_recebimento"]]
        )
    else:
        st.write("Tudo pago! ✅")

    st.subheader("🔥 Mapa de Calor do Mercado (ticket médio por especificidade)")
    ticket_medio = df.groupby("especificidade")["cache_total"].mean().sort_values(ascending=False)
    st.bar_chart(ticket_medio)

    st.subheader("📣 Canal de Aquisição mais lucrativo")
    st.caption("De onde vêm os clientes que pagam melhor.")
    ticket_por_canal = df.groupby("canal_aquisicao")["cache_total"].mean().sort_values(ascending=False)
    st.bar_chart(ticket_por_canal)

    st.subheader("⏰ Prazos de Entrega Mais Próximos")
    prazos = df[["nome_projeto", "nome_cliente", "data_entrega_combinada"]].dropna()
    prazos = prazos.sort_values("data_entrega_combinada")
    st.dataframe(prazos)
