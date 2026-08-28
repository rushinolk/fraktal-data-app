"""
ui/financeiro.py
-----------------
Módulo CONSUMIDOR puro: cards de resumo, previsibilidade de caixa, painel
de cobrança e prazos de entrega. Fica no Streamlit porque é operacional
(o amigo usa no dia a dia) -- análise/gráfico de mercado saiu daqui, vira
responsabilidade da camada OLAP/apresentação, fora do app.

Sem gráfico nesta tela: Previsibilidade de Caixa virou tabela (data +
soma prevista), suficiente pra planejamento sem ser uma peça de análise.
"""

import streamlit as st

from data_layer import buscar_trabalhos
from ui.helpers import formatar_reais, formatar_colunas_data


def render():
    st.header("Financeiro")

    df = buscar_trabalhos()

    if df.empty:
        st.info("Ainda não há registros. Adicione o primeiro na aba 'Novo Registro'.")
        return

    df["taxa_cambio"] = df["taxa_cambio"].fillna(1.0)
    df["cache_total_brl"] = df["cache_total"] * df["taxa_cambio"]
    df["lucro"] = df["cache_total_brl"] - df["custos_operacao"].fillna(0)

    total_faturado = df["cache_total_brl"].sum()
    total_recebido = df.loc[df["status_pagamento"] == "Totalmente Pago", "cache_total_brl"].sum()
    total_pendente = total_faturado - total_recebido
    lucro_total = df["lucro"].sum()

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("💰 Total Faturado", formatar_reais(total_faturado))
    col_b.metric("✅ Já Recebido", formatar_reais(total_recebido))
    col_c.metric("⏳ Pendente de Receber", formatar_reais(total_pendente))
    col_d.metric("📈 Lucro Total", formatar_reais(lucro_total))
    st.caption("Valores em Real — clientes que pagaram em dólar/euro já convertidos pela taxa de câmbio informada no registro.")

    st.divider()

    pendentes = df[df["status_pagamento"] != "Totalmente Pago"].copy()

    st.subheader("📅 Previsibilidade de Caixa")
    if not pendentes.empty:
        caixa_futuro = (
            pendentes.groupby("previsao_recebimento")["cache_total_brl"]
            .sum()
            .reset_index()
            .rename(columns={"previsao_recebimento": "data_prevista", "cache_total_brl": "valor_previsto"})
            .sort_values("data_prevista")
        )
        caixa_futuro = formatar_colunas_data(caixa_futuro, ["data_prevista"])
        caixa_futuro["valor_previsto"] = caixa_futuro["valor_previsto"].apply(formatar_reais)
        st.dataframe(caixa_futuro, hide_index=True, use_container_width=True)
    else:
        st.write("Nenhum recebimento pendente no momento.")

    st.subheader("📋 Painel de Cobrança")
    if not pendentes.empty:
        exibicao = pendentes[
            ["nome_cliente", "nome_projeto", "moeda", "cache_total", "cache_total_brl", "status_pagamento", "previsao_recebimento"]
        ].rename(columns={"cache_total": "valor_original", "cache_total_brl": "valor_em_real"})
        exibicao = formatar_colunas_data(exibicao, ["previsao_recebimento"])
        st.dataframe(exibicao, hide_index=True, use_container_width=True)
    else:
        st.write("Tudo pago! ✅")

    st.subheader("⏰ Prazos de Entrega Mais Próximos")
    prazos = df[["nome_projeto", "nome_cliente", "data_entrega_combinada"]].dropna()
    prazos = prazos.sort_values("data_entrega_combinada")
    prazos = formatar_colunas_data(prazos, ["data_entrega_combinada"])
    st.dataframe(prazos, hide_index=True, use_container_width=True)
