"""
ui/helpers.py
--------------
Funções e constantes pequenas, compartilhadas entre os módulos de UI
(formulário, pipeline, dashboard), para não duplicar código entre eles.
"""

from niches_config import NICHOS_PADRAO
from data_layer import buscar_nichos_existentes

NOVO_NICHO_LABEL = "+ Adicionar novo nicho..."
OUTRO_CANAL_LABEL = "Outro (digitar)"


def obter_opcoes_nicho() -> list:
    """
    Monta a lista de nichos pro dropdown: os padrão + os que já apareceram
    em registros salvos + a opção de cadastrar um nicho novo no final.
    """
    nichos_ja_usados = buscar_nichos_existentes()
    opcoes = sorted(set(NICHOS_PADRAO) | set(nichos_ja_usados))
    opcoes.append(NOVO_NICHO_LABEL)
    return opcoes


def formatar_reais(valor: float) -> str:
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return f"R$ {texto}"
