"""
scoring.py — Algoritmo de priorização de telefones para disparo WhatsApp
Prefeitura do Rio de Janeiro — Desafio Técnico DS
"""

import numpy as np
import pandas as pd
from scipy import stats


def wilson_lower_bound(positives: int, total: int, confidence: float = 0.95) -> float:
    """
    Limite inferior do intervalo de confiança de Wilson para proporções.
    Mais robusto que a taxa simples para amostras com volumes diferentes.
    """
    if total == 0:
        return 0.0
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    phat = positives / total
    denominator = 1 + z**2 / total
    center = phat + z**2 / (2 * total)
    margin = z * np.sqrt(phat * (1 - phat) / total + z**2 / (4 * total**2))
    return (center - margin) / denominator


def calcular_score_telefone(
    row: pd.Series,
    sistema_scores: dict,
    hoje: pd.Timestamp = None,
    peso_sistema: float = 0.50,
    peso_frescor: float = 0.40,
    peso_ddd: float = 0.10,
    ddd_preferencial: str = "21",
) -> float:
    """
    Combina sistema de origem, frescor temporal e DDD em um score 0-1.
    Parâmetros de peso devem somar 1.0.
    """
    if hoje is None:
        hoje = pd.Timestamp.now()

    # 1. Score do Sistema (Qualidade da fonte)
    score_sistema = sistema_scores.get(row["id_sistema_mask"], 0.0)

    # 2. Score de Frescor (Decai exponencialmente com o tempo)
    data_atualizacao = pd.to_datetime(row["registro_data_atualizacao"])
    dias = (hoje - data_atualizacao).days
    # Meia-vida de ~1 ano (365 dias)
    score_frescor = np.exp(-max(0, dias) / 365)

    # 3. Score de DDD (Preferência local)
    ddd = str(row.get("ddd", ""))
    score_ddd = 1.0 if ddd == ddd_preferencial else 0.7

    # Cálculo final ponderado
    score_final = (
        peso_sistema * score_sistema +
        peso_frescor * score_frescor +
        peso_ddd * score_ddd
    )

    return float(np.round(score_final, 4))


def selecionar_top_n(
    df: pd.DataFrame,
    id_cidadao_col: str,
    score_col: str = "score",
    n: int = 2,
) -> pd.DataFrame:
    """
    Retorna os N telefones com maior score por cidadão.
    """
    return (
        df.sort_values(score_col, ascending=False)
        .groupby(id_cidadao_col)
        .head(n)
        .reset_index(drop=True)
    )
