"""
ui/pipeline.py
--------------
Módulo híbrido: PRODUTOR (formulário pra adicionar item ao pipeline) e
CONSUMIDOR (tabela editável). A partir da v4, nicho passou a ser FK pra
tabela `nichos` -- o dropdown mostra o nome, mas guarda/edita o id por
baixo (mapeamento feito aqui, não no data_layer).
"""

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
    else:
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
