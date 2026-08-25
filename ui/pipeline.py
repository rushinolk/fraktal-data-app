"""
ui/pipeline.py
--------------
Módulo híbrido: PRODUTOR (formulário pra adicionar um novo item ao pipeline)
e CONSUMIDOR (tabela editável mostrando os itens já cadastrados). Faz sentido
ser híbrido aqui porque a natureza do pipeline é justamente acompanhar e
atualizar status ao longo do tempo -- diferente do formulário de registro
(só produtor) e do dashboard (só consumidor).
"""

import streamlit as st

from data_layer import buscar_pipeline, salvar_pipeline_item, atualizar_pipeline_completo
from opcoes import STATUS_PIPELINE
from ui.helpers import obter_opcoes_nicho


def render():
    st.header("Projetos em Aberto")
    st.caption(
        "Artistas, clientes ou negociações que você está de olho, antes de virar um contrato fechado. "
        "Isso é separado dos registros de trabalhos já executados."
    )

    with st.expander("➕ Adicionar novo item ao pipeline"):
        opcoes_nicho = obter_opcoes_nicho()

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            nome_contato_pipeline = st.text_input("Nome do Artista/Cliente", key="pipeline_nome")
        with col_p2:
            nicho_pipeline = st.selectbox("Nicho de Mercado", opcoes_nicho, key="pipeline_nicho")
        with col_p3:
            status_pipeline = st.selectbox("Status", STATUS_PIPELINE, key="pipeline_status")

        col_p4, col_p5 = st.columns(2)
        with col_p4:
            valor_estimado_pipeline = st.number_input(
                "Valor Estimado (R$, opcional)", min_value=0.0, step=50.0, key="pipeline_valor"
            )
        with col_p5:
            data_prevista_pipeline = st.date_input(
                "Data Prevista do Evento (opcional)", key="pipeline_data"
            )

        observacoes_pipeline = st.text_area("Observações", key="pipeline_obs")

        if st.button("Adicionar ao Pipeline"):
            if not nome_contato_pipeline:
                st.error("Preencha o nome do artista/cliente antes de adicionar.")
            else:
                salvar_pipeline_item({
                    "nome_contato": nome_contato_pipeline,
                    "nicho_mercado": nicho_pipeline,
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
                "nome_contato": "Artista/Cliente",
                "nicho_mercado": "Nicho",
                "valor_estimado": st.column_config.NumberColumn("Valor Estimado (R$)", format="R$ %.2f"),
                "data_prevista": "Data Prevista",
                "observacoes": "Observações",
            },
            num_rows="dynamic",
            use_container_width=True,
            key="editor_pipeline",
        )

        if st.button("💾 Salvar alterações no Pipeline"):
            atualizar_pipeline_completo(df_pipeline_editado)
            st.success("Pipeline atualizado!")
            st.rerun()
