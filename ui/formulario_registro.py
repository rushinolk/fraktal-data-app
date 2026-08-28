"""
ui/formulario_registro.py
--------------------------
Módulo PRODUTOR de dados: formulário onde o usuário registra um trabalho
executado. A partir da v4, os catálogos (nicho, tipo de cliente, canal,
serviço, especificidade, pessoas/funções da equipe) vêm do banco via
data_layer -- nada de "+ Adicionar novo" aqui, esses catálogos são
geridos pelo Arthur direto no Supabase.

Os antigos campos de Horas de Captação/Edição e Tamanho de Equipe saíram
-- viraram a seção "Equipe envolvida" (quem participou, função, cachê e
benefícios recebidos).
"""

from datetime import date
import pandas as pd
import streamlit as st

from data_layer import (
    registrar_trabalho,
    buscar_nichos,
    buscar_tipos_cliente,
    buscar_canais_aquisicao,
    buscar_servicos,
    buscar_especificidades,
    buscar_pessoas_equipe,
    buscar_funcoes_equipe,
)
from opcoes import STATUS_PAGAMENTO, MOEDAS


def render():
    st.header("Registrar novo trabalho")

    nichos = buscar_nichos()
    if not nichos:
        st.error("Nenhum nicho cadastrado ainda. Peça pro Arthur cadastrar em `nichos` no Supabase.")
        return

    nicho_por_nome = {n["nome"]: n for n in nichos}

    col_data, _ = st.columns([1, 2])
    with col_data:
        data_execucao = st.date_input("Data de Execução", value=date.today(), format="DD/MM/YYYY")

    st.divider()

    col_nicho, col_cliente = st.columns(2)

    with col_nicho:
        nome_nicho = st.selectbox("Nicho de Mercado", list(nicho_por_nome.keys()))
        nicho = nicho_por_nome[nome_nicho]

        tipos_cliente = buscar_tipos_cliente(nicho["id"])
        tipo_cliente = None
        if tipos_cliente:
            tipo_por_nome = {t["nome"]: t for t in tipos_cliente}
            escolha_tipo = st.selectbox("Tipo de Cliente", list(tipo_por_nome.keys()))
            tipo_cliente = tipo_por_nome[escolha_tipo]

        especificidades = buscar_especificidades(nicho["id"])
        especificidade_ids = []
        especificidade_texto = ""
        if especificidades:
            espec_por_nome = {e["nome"]: e for e in especificidades}
            label = nicho.get("especificidade_label") or "Especificidade"
            if nicho.get("especificidade_multipla"):
                escolhidas = st.multiselect(label, list(espec_por_nome.keys()))
            else:
                escolhida = st.selectbox(label, list(espec_por_nome.keys()))
                escolhidas = [escolhida] if escolhida else []
            especificidade_ids = [espec_por_nome[e]["id"] for e in escolhidas]
            especificidade_texto = ", ".join(escolhidas)
        else:
            st.caption("ℹ️ Esse nicho ainda não tem especificidades cadastradas.")

    evento_obrigatorio = bool(nicho.get("evento_obrigatorio"))
    incluir_cliente_no_nome = bool(tipo_cliente.get("incluir_no_nome_projeto")) if tipo_cliente else True

    with col_cliente:
        nome_cliente = st.text_input("Nome do Cliente/DJ/Artista/Contratante")

        label_evento = "Nome do Evento" + (" *" if evento_obrigatorio else " (opcional)")
        nome_evento = st.text_input(
            label_evento,
            placeholder="Ex: Infected, Casa Aberta, Lançamento X",
            help="Obrigatório para esse nicho." if evento_obrigatorio else None,
        )

        canais = buscar_canais_aquisicao()
        canal_por_nome = {c["nome"]: c for c in canais}
        nome_canal = st.selectbox("Canal de Aquisição", list(canal_por_nome.keys()))
        canal = canal_por_nome[nome_canal]

    servicos = buscar_servicos()
    servico_por_nome = {s["nome"]: s for s in servicos}
    servicos_escolhidos = st.multiselect(
        "Serviços Entregues (o pacote combinado costuma juntar mais de um)",
        list(servico_por_nome.keys()),
    )
    servico_ids = [servico_por_nome[s]["id"] for s in servicos_escolhidos]

    ano_execucao = data_execucao.year
    if nome_evento:
        partes = ([nome_cliente] if incluir_cliente_no_nome else []) + [nome_evento, str(ano_execucao)]
        sugestao_nome = " ".join([p for p in partes if p])
    else:
        partes_sugestao = [p for p in [nome_cliente, especificidade_texto or nome_nicho] if p]
        partes_sugestao.append(data_execucao.strftime("%d/%m/%Y"))
        sugestao_nome = " - ".join(partes_sugestao)

    nome_projeto = st.text_input(
        "Nome do Projeto", value=sugestao_nome, help="Sugestão automática — pode editar à vontade."
    )

    st.divider()

    st.subheader("👥 Equipe envolvida")
    st.caption(
        "Quem participou desse trabalho, em que função, e o que recebeu (cachê e/ou "
        "benefícios cedidos pelo contratante — transporte, alimentação, consumação, ingresso)."
    )

    pessoas = buscar_pessoas_equipe()
    funcoes = buscar_funcoes_equipe()
    nomes_pessoas = [p["nome"] for p in pessoas]
    nomes_funcoes = [f["nome"] for f in funcoes]

    if not pessoas:
        st.warning("Nenhuma pessoa cadastrada em `pessoas_equipe` ainda — peça pro Arthur cadastrar.")

    modelo_equipe = pd.DataFrame([{
        "pessoa": nomes_pessoas[0] if nomes_pessoas else "",
        "funcao": "",
        "cache_pago": 0.0,
        "transporte": False,
        "alimentacao": False,
        "consumacao": False,
        "ingresso": False,
    }])

    equipe_editada = st.data_editor(
        modelo_equipe,
        column_config={
            "pessoa": st.column_config.SelectboxColumn("Pessoa", options=nomes_pessoas, required=True),
            "funcao": st.column_config.SelectboxColumn("Função", options=[""] + nomes_funcoes),
            "cache_pago": st.column_config.NumberColumn("Cachê Pago (R$, opcional)", min_value=0.0, format="%.2f"),
            "transporte": st.column_config.CheckboxColumn("Transporte"),
            "alimentacao": st.column_config.CheckboxColumn("Alimentação"),
            "consumacao": st.column_config.CheckboxColumn("Consumação"),
            "ingresso": st.column_config.CheckboxColumn("Ingresso"),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_equipe",
    )

    st.divider()

    col_moeda, col_taxa = st.columns(2)
    with col_moeda:
        moeda = st.selectbox("Moeda do Pacote", MOEDAS, help="Clientes de fora do Brasil às vezes fecham em dólar ou euro.")
    with col_taxa:
        if moeda != "BRL":
            taxa_cambio = st.number_input(
                f"Taxa de Câmbio (1 {moeda} = quantos R$)", min_value=0.0, step=0.01, value=5.0
            )
        else:
            taxa_cambio = 1.0
            st.caption("Sem conversão necessária — pacote já fechado em Real.")

    col3, col4 = st.columns(2)
    with col3:
        cache_total = st.number_input(f"Valor do Pacote Negociado ({moeda})", min_value=0.0, step=50.0)
    with col4:
        custos_operacao = st.number_input(
            "Custos de Operação (R$)",
            min_value=0.0,
            step=10.0,
            help="Sempre em Real — gastos diretos (Uber, gasolina, material...). Cachê da equipe entra na seção acima, não aqui.",
        )

    col5, col6, col7 = st.columns(3)
    with col5:
        status_pagamento = st.selectbox("Status do Pagamento", STATUS_PAGAMENTO)
    with col6:
        previsao_recebimento = st.date_input("Previsão de Recebimento", format="DD/MM/YYYY")
    with col7:
        data_entrega_combinada = st.date_input("Prazo de Entrega Combinado", format="DD/MM/YYYY")

    st.divider()

    if st.button("💾 Salvar Registro", use_container_width=True):
        erros = []
        if not nome_projeto:
            erros.append("Preencha o nome do projeto.")
        if not nome_cliente:
            erros.append("Preencha o nome do cliente.")
        if evento_obrigatorio and not nome_evento:
            erros.append(f"Nome do Evento é obrigatório para o nicho '{nome_nicho}'.")
        if moeda != "BRL" and taxa_cambio <= 0:
            erros.append("Informe uma taxa de câmbio válida pra converter o valor pra Real.")

        pessoa_id_por_nome = {p["nome"]: p["id"] for p in pessoas}
        funcao_id_por_nome = {f["nome"]: f["id"] for f in funcoes}

        equipe_payload = []
        for _, linha in equipe_editada.iterrows():
            nome_pessoa = linha.get("pessoa")
            if not nome_pessoa:
                continue
            if nome_pessoa not in pessoa_id_por_nome:
                erros.append(f"Pessoa '{nome_pessoa}' não encontrada no catálogo.")
                continue
            equipe_payload.append({
                "pessoa_id": pessoa_id_por_nome[nome_pessoa],
                "funcao_id": funcao_id_por_nome.get(linha.get("funcao")) if linha.get("funcao") else None,
                "cache_pago": linha.get("cache_pago") or None,
                "recebeu_transporte": bool(linha.get("transporte")),
                "recebeu_alimentacao": bool(linha.get("alimentacao")),
                "recebeu_consumacao": bool(linha.get("consumacao")),
                "recebeu_ingresso": bool(linha.get("ingresso")),
            })

        if erros:
            for erro in erros:
                st.error(erro)
        else:
            payload = {
                "cliente_nome": nome_cliente,
                "nicho_id": nicho["id"],
                "tipo_cliente_id": tipo_cliente["id"] if tipo_cliente else None,
                "canal_aquisicao_id": canal["id"],
                "nome_projeto": nome_projeto,
                "nome_evento": nome_evento or None,
                "data_execucao": str(data_execucao),
                "moeda": moeda,
                "taxa_cambio": taxa_cambio,
                "cache_total": cache_total,
                "custos_operacao": custos_operacao,
                "status_pagamento": status_pagamento,
                "previsao_recebimento": str(previsao_recebimento),
                "data_entrega_combinada": str(data_entrega_combinada),
                "servico_ids": servico_ids,
                "especificidade_ids": especificidade_ids,
                "equipe": equipe_payload,
            }
            registrar_trabalho(payload)
            st.success("Registro salvo com sucesso!")
            st.balloons()
