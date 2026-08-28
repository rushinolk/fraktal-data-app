"""
opcoes.py
---------
A partir da v4, os catálogos de negócio (nicho, tipo de cliente, canal,
serviço, especificidade, pessoas/funções da equipe) moraram pro banco
(tabelas próprias, geridas direto no Supabase) -- ver data_layer.py.

Este arquivo agora só guarda os domínios REALMENTE fixos, pequenos o
bastante pra não merecerem uma tabela: status de pagamento, status do
pipeline e moedas aceitas. Se um desses crescer/mudar de frequência,
vale reavaliar e mover pra uma tabela também.
"""

STATUS_PAGAMENTO = ["Pendente", "50% Pago", "Totalmente Pago"]

STATUS_PIPELINE = [
    "Mapeado",
    "Em Conversa",
    "Proposta Enviada",
    "Fechado",
    "Perdido",
]

MOEDAS = ["BRL", "USD", "EUR"]
