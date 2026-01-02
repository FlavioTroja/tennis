import pandas as pd

EDGE_THRESHOLD = 0.03   # 3% minimo


def implied_prob(decimal_odds: float) -> float:
    return 1.0 / decimal_odds


def compute_edge(prob: float, odds: float) -> float:
    return prob - implied_prob(odds)


def evaluate_matches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input df REQUIRED columns:
    - prob_a
    - prob_b
    - odds_player_a
    - odds_player_b
    """

    df = df.copy()

    df["edge_a"] = df.apply(
        lambda r: compute_edge(r.prob_a, r.odds_player_a),
        axis=1
    )

    df["edge_b"] = df.apply(
        lambda r: compute_edge(r.prob_b, r.odds_player_b),
        axis=1
    )

    df["bet_a"] = df["edge_a"] >= EDGE_THRESHOLD
    df["bet_b"] = df["edge_b"] >= EDGE_THRESHOLD

    return df
