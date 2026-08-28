"""
ui/pipeline.py
--------------
Módulo híbrido: PRODUTOR (formulário pra adicionar item ao pipeline) e
CONSUMIDOR (tabela editável). Nicho é FK pra tabela `nichos`.

Inclui a conversão Pipeline -> Novo Registro: marca o item como "Fechado"
(mantém histórico, não apaga) e pré-preenche cliente/nicho/valor no
formulário via st.session_state -- evita digitar os dados do cliente
de novo.
"""

import pandas as pd
import streamlit as st

from data_layer import buscar_pipeline, salvar_pipeline_item, atualizar_pipeline_completo, buscar_nichos
from opcoes import STATUS_PIPELINE


def render():
    st.header("Projetos em Aberto")
    st.caption(
        "Artistas, clientes ou negociações que você está de olho, antes de virar um contrato fechado. "
        "Isso é separado dos registros de trabalhos já executados."
    )

    nichos = buscar_nichos()
    nomes_nicho = [n["nome"] for n in nichos]
    id_por_nome_nicho = {n["nome"]: n["id"] for n in nichos}

    with st.expander("➕ Adicionar novo item ao pipeline"):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            nome_contato_pipeline = st.text_input("Nome do Artista/Cliente", key="pipeline_nome")
        with col_p2:
            nicho_nome_pipeline = st.selectbox("Nicho de Mercado", nomes_nicho, key="pipeline_nicho")
        with col_p3:
            status_pipeline = st.selectbox("Status", STATUS_PIPELINE, key="pipeline_status")

        col_p4, col_p5 = st.columns(2)
        with col_p4:
            valor_estimado_pipeline = st.number_input(
                "Valor Estimado (R$, opcional)", min_value=0.0, step=50.0, key="pipeline_valor"
            )
        with col_p5:
            data_prevista_pipeline = st.date_input(
                "Data Prevista do Evento (opcional)", key="pipeline_data", format="DD/MM/YYYY"
            )

        observacoes_pipeline = st.text_area("Observações", key="pipeline_obs")

        if st.button("Adicionar ao Pipeline"):
            if not nome_contato_pipeline:
                st.error("Preencha o nome do artista/cliente antes de adicionar.")
            else:
                salvar_pipeline_item({
                    "nome_contato": nome_contato_pipeline,
                    "nicho_id": id_por_nome_nicho.get(nicho_nome_pipeline),
                    "status": status_pipeline,
                    "valor_estimado": valor_estimado_pipeline,
                    "data_prevista": str(data_prevista_pipeline),
                    "observacoes": observacoes_pipeline,
                })
                st.success("Adicionado ao pipeline!")
                st.rerun()

    st.divider()

    df_pipeline = buscar_pipeline()

    if df_pipeline.empty:
        st.info("Nenhum item no pipeline ainda. Adicione o primeiro acima.")
        return

    st.write("Edite direto na tabela abaixo (clique numa célula pra mudar status, valor, etc.) e depois clique em Salvar.")
    df_pipeline_editado = st.data_editor(
        df_pipeline,
        column_config={
            "status": st.column_config.SelectboxColumn("Status", options=STATUS_PIPELINE),
            "nicho_mercado": st.column_config.SelectboxColumn("Nicho", options=nomes_nicho),
            "nome_contato": "Artista/Cliente",
            "valor_estimado": st.column_config.NumberColumn("Valor Estimado (R$)", format="R$ %.2f"),
            "data_prevista": st.column_config.DateColumn("Data Prevista", format="DD/MM/YYYY"),
            "observacoes": "Observações",
        },
        num_rows="dynamic",
        use_container_width=True,
        key="editor_pipeline",
    )

    if st.button("💾 Salvar alterações no Pipeline"):
        df_para_salvar = df_pipeline_editado.copy()
        df_para_salvar["nicho_id"] = df_para_salvar["nicho_mercado"].map(id_por_nome_nicho)
        atualizar_pipeline_completo(df_para_salvar)
        st.success("Pipeline atualizado!")
        st.rerun()

    st.divider()

    # ------------------------------------------------------------
    # Conversão Pipeline -> Novo Registro: evita digitar os dados
    # do cliente de novo quando a negociação fecha de verdade.
    # ------------------------------------------------------------
    st.subheader("✅ Fechar negociação")
    st.caption(
        "Escolha um item do pipeline pra pré-preencher o formulário de Novo Registro. "
        "O item é marcado como 'Fechado' aqui (fica no histórico), e você completa o resto lá."
    )

    df_convertivel = df_pipeline[~df_pipeline["status"].isin(["Fechado", "Perdido"])].reset_index(drop=True)

    if df_convertivel.empty:
        st.caption("Nenhum item em aberto pra converter no momento.")
    else:
        opcoes_conversao = [
            f"{row.nome_contato} — {row.nicho_mercado} ({row.status})"
            for row in df_convertivel.itertuples()
        ]
        escolha_pos = st.selectbox(
            "Item do pipeline",
            options=list(range(len(opcoes_conversao))),
            format_func=lambda i: opcoes_conversao[i],
            key="pipeline_conversao_escolha",
        )

        if st.button("➡️ Preencher Novo Registro com esses dados"):
            linha = df_convertivel.iloc[escolha_pos]

            st.session_state["form_nome_cliente"] = linha["nome_contato"]
            if linha["nicho_mercado"] in nomes_nicho:
                st.session_state["form_nicho"] = linha["nicho_mercado"]
            if pd.notna(linha["valor_estimado"]):
                st.session_state["form_cache_total"] = float(linha["valor_estimado"])

            # Marca como Fechado no pipeline em vez de apagar -- mantém histórico.
            df_atualizado = df_pipeline.copy()
            filtro = (
                (df_atualizado["nome_contato"] == linha["nome_contato"])
                & (df_atualizado["nicho_mercado"] == linha["nicho_mercado"])
            )
            df_atualizado.loc[filtro, "status"] = "Fechado"
            df_atualizado["nicho_id"] = df_atualizado["nicho_mercado"].map(id_por_nome_nicho)
            atualizar_pipeline_completo(df_atualizado)

            st.success("Dados prontos! Vá até a aba '📝 Novo Registro' pra completar e salvar.")
            st.rerun()
