"""
niches_config.py
-----------------
Esta é a ÚNICA tabela que precisa ser editada quando um novo nicho de
mercado ganhar perguntas específicas (tipo de cliente, especificidade).

Para adicionar um nicho novo com perguntas próprias no futuro (ex: "Casamentos"),
basta adicionar uma nova entrada no dicionário NICHOS_CONFIG abaixo --
o app.py e o data_layer.py não precisam ser alterados.

Se um nicho NÃO estiver aqui (por exemplo, porque ele acabou de ser criado
digitando no formulário), o app simplesmente não pergunta Tipo de Cliente
nem Especificidade -- usa só os campos padrão de qualquer registro.
"""

NICHOS_CONFIG = {
    "Música Eletrônica": {
        "tipo_cliente_options": ["Produtora", "DJ", "Agência"],
        "especificidade_label": "Vertente Musical",
        "especificidade_type": "text",  # "text" ou "select"
        "especificidade_placeholder": "Ex: Tech House, Psytrance",
    },
    "Mercado Imobiliário": {
        "tipo_cliente_options": ["Corretor Autônomo", "Imobiliária", "Construtora"],
        "especificidade_label": "Tipo de Captação",
        "especificidade_type": "select",
        "especificidade_options": ["Casa/Apto", "Terreno", "Acompanhamento de Obra"],
    },
    # Exemplo de como adicionar um nicho novo no futuro:
    # "Casamentos": {
    #     "tipo_cliente_options": ["Noivos", "Cerimonialista", "Buffet/Espaço"],
    #     "especificidade_label": "Tipo de Cobertura",
    #     "especificidade_type": "select",
    #     "especificidade_options": ["Cerimônia completa", "Só making of", "Só festa"],
    # },
}

# Nichos que sempre aparecem no dropdown, mesmo que ainda não tenham
# nenhum registro salvo na planilha.
NICHOS_PADRAO = ["Música Eletrônica", "Mercado Imobiliário"]


def get_config(nicho: str):
    """Retorna a configuração de perguntas extras de um nicho, ou None se não existir."""
    return NICHOS_CONFIG.get(nicho)
