"""
opcoes.py
---------
Listas de opções usadas em campos do formulário que NÃO dependem do nicho
de mercado (diferente do niches_config.py, que é só sobre isso).

Para adicionar uma opção nova de canal de aquisição, basta incluir na lista abaixo.
"""

CANAIS_AQUISICAO = [
    "Indicação",
    "Instagram",
    "Evento Anterior",
    "Prospecção Ativa",
    "Já era Cliente",
]

STATUS_PIPELINE = [
    "Mapeado",
    "Em Conversa",
    "Proposta Enviada",
    "Fechado",
    "Perdido",
]
