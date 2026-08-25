"""
ui/formulario_registro.py
--------------------------
Módulo PRODUTOR de dados: o formulário onde o usuário registra um
trabalho já executado. Só escreve na planilha (via data_layer.salvar_registro),
nunca lê para gerar gráficos ou análises -- essa responsabilidade é do
módulo ui/dashboard.py.
"""

from datetime import date
import streamlit as st

from data_layer import salvar_registro
from niches_config import get_config
from opcoes import CANAIS_AQUISICAO
from ui.helpers import NOVO_NICHO_LABEL, OUTRO_CANAL_LABEL, obter_opcoes_nicho


def render():
    st.header("Registrar novo trabalho")

    col_data, col_espaco = st.columns([1, 2])
    with col_data:
        data_execucao = st.date_input("Data de Execução", value=date.today())

    st.divider()

    # Bloco 2: Inteligência Comercial (aqui mora a condicional)
    col_nicho, col_cliente = st.columns(2)

    with col_nicho:
        # O dropdown junta os nichos padrão + os que já apareceram em registros
        # salvos anteriormente, sempre em ordem alfabética, e no fim oferece a
        # opção de cadastrar um nicho totalmente novo.
        opcoes_nicho = obter_opcoes_nicho()
        escolha_nicho = st.selectbox("Nicho de Mercado", opcoes_nicho)

        if escolha_nicho == NOVO_NICHO_LABEL:
            nicho_mercado = st.text_input("Nome do novo nicho de mercado").strip()
        else:
            nicho_mercado = escolha_nicho

    with col_cliente:
        nome_cliente = st.text_input("Nome do Cliente/DJ/Artista/Contratante")
        nome_evento = st.text_input(
            "Nome do Evento (opcional)",
            placeholder="Ex: Infected, Casa Aberta, Lançamento X",
            help="Se o trabalho tiver um nome de evento/festa/campanha, coloque aqui — ajuda a montar o nome do projeto.",
        )

        # Canal de Aquisição: lista fixa + opção de digitar algo novo
        escolha_canal = st.selectbox("Canal de Aquisição", CANAIS_AQUISICAO + [OUTRO_CANAL_LABEL])
        if escolha_canal == OUTRO_CANAL_LABEL:
            canal_aquisicao = st.text_input("Qual canal de aquisição?").strip()
        else:
            canal_aquisicao = escolha_canal

    # Consulta se esse nicho tem perguntas específicas configuradas.
    # Se não tiver (nicho novo ou ainda sem configuração), não força
    # nenhum campo extra -- só os campos padrão do registro.
    config_nicho = get_config(nicho_mercado) if nicho_mercado else None

    tipo_cliente = None
    especificidade = None

    if config_nicho:
        col_tipo, col_espec = st.columns(2)
        with col_tipo:
            tipo_cliente = st.selectbox("Tipo de Cliente", config_nicho["tipo_cliente_options"])
        with col_espec:
            if config_nicho["especificidade_type"] == "select":
                especificidade = st.selectbox(
                    config_nicho["especificidade_label"],
                    config_nicho["especificidade_options"],
                )
            else:
                especificidade = st.text_input(
                    config_nicho["especificidade_label"],
                    placeholder=config_nicho.get("especificidade_placeholder", ""),
                )
    elif nicho_mercado:
        st.caption(
            "ℹ️ Esse nicho ainda não tem perguntas específicas configuradas — "
            "usando apenas os campos padrão."
        )

    servicos_entregues = st.multiselect(
        "Serviços Entregues (o pacote combinado costuma juntar mais de um)",
        ["Aftermovie", "Fotos", "Voo de Drone", "Reels"],
    )

    # Sugestão automática de nome do projeto. Se tiver nome de evento
    # preenchido, segue o padrão "Cliente/DJ + Evento + Ano" (ex: "Dezzert
    # Infected 2025"). Caso contrário, usa o formato genérico anterior.
    ano_execucao = data_execucao.year

    if nome_evento:
        sugestao_nome = " ".join([p for p in [nome_cliente, nome_evento, str(ano_execucao)] if p])
    else:
        partes_sugestao = [p for p in [nome_cliente, especificidade or nicho_mercado] if p]
        partes_sugestao.append(data_execucao.strftime("%d/%m/%Y"))
        sugestao_nome = " - ".join(partes_sugestao)

    nome_projeto = st.text_input(
        "Nome do Projeto",
        value=sugestao_nome,
        help="Sugestão automática (Cliente/DJ + Evento + Ano, quando houver) — pode editar à vontade.",
    )

    st.divider()

    # Bloco 3: Esforço e Tempo
    st.caption(
        "📌 Os campos abaixo são só para o SEU controle interno (calcular se o pacote valeu a pena). "
        "Ele continua fechando por valor de pacote, não por hora."
    )
    col1, col2, col_equipe = st.columns(3)
    with col1:
        horas_captacao = st.number_input("Horas de Captação", min_value=0.0, step=0.5)
    with col2:
        horas_edicao = st.number_input("Horas de Edição", min_value=0.0, step=0.5)
    with col_equipe:
        tamanho_equipe = st.number_input(
            "Pessoas na Equipe (incluindo você)",
            min_value=1,
            value=1,
            step=1,
        )

    st.divider()

    # Bloco 4: Controle de Caixa
    col3, col4 = st.columns(2)
    with col3:
        cache_total = st.number_input("Valor do Pacote Negociado (R$)", min_value=0.0, step=50.0)
    with col4:
        custos_operacao = st.number_input("Custos de Operação (R$)", min_value=0.0, step=10.0)

    col5, col6, col7 = st.columns(3)
    with col5:
        status_pagamento = st.selectbox(
            "Status do Pagamento", ["Pendente", "50% Pago", "Totalmente Pago"]
        )
    with col6:
        previsao_recebimento = st.date_input("Previsão de Recebimento")
    with col7:
        data_entrega_combinada = st.date_input("Prazo de Entrega Combinado")

    st.divider()

    if st.button("💾 Salvar Registro", use_container_width=True):
        if not nome_projeto:
            st.error("Preencha o nome do projeto antes de salvar.")
        elif not nicho_mercado:
            st.error("Digite o nome do novo nicho de mercado antes de salvar.")
        elif not canal_aquisicao:
            st.error("Digite o canal de aquisição antes de salvar.")
        else:
            registro = {
                "nome_projeto": nome_projeto,
                "data_execucao": str(data_execucao),
                "nicho_mercado": nicho_mercado,
                "tipo_cliente": tipo_cliente,
                "nome_cliente": nome_cliente,
                "nome_evento": nome_evento,
                "canal_aquisicao": canal_aquisicao,
                "servicos_entregues": ", ".join(servicos_entregues),
                "especificidade": especificidade,
                "horas_captacao": horas_captacao,
                "horas_edicao": horas_edicao,
                "tamanho_equipe": tamanho_equipe,
                "cache_total": cache_total,
                "custos_operacao": custos_operacao,
                "status_pagamento": status_pagamento,
                "previsao_recebimento": str(previsao_recebimento),
                "data_entrega_combinada": str(data_entrega_combinada),
            }
            salvar_registro(registro)
            st.success("Registro salvo com sucesso!")
            st.balloons()
