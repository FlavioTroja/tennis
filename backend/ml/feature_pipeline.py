import pandas as pd

from app.services.feature_service import (
    get_player_id,
    get_surface_state,
    # get_form,
    # get_h2h,
)

# ⚠️ QUI DEFINISCI LE FEATURE DEL MODELLO
FEATURE_COLUMNS = [
    "elo_diff",
    # "surface_elo_diff",
    # "recent_5_diff",
    # "recent_10_diff",
    # "h2h_diff",
]


def compute_features_row(
    player_a: str,
    player_b: str,
    surface: str,
) -> dict:
    """
    Calcola le feature per UNA partita.
    Usata da API /predict e odds pipeline.
    """

    A = get_player_id(player_a)
    B = get_player_id(player_b)

    elo_A, _ = get_surface_state(A, surface)
    elo_B, _ = get_surface_state(B, surface)

    features = {
        "elo_diff": elo_A - elo_B,
    }

    return features


def compute_features_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola le feature per un DataFrame di match.
    Usata da odds pipeline e backtest.
    """

    rows = []

    for _, r in df.iterrows():
        features = compute_features_row(
            player_a=r.player_a,
            player_b=r.player_b,
            surface=r.surface,
        )

        rows.append({**r.to_dict(), **features})

    return pd.DataFrame(rows)


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Restituisce SOLO le colonne feature
    (ordine garantito per sklearn)
    """
    return df[FEATURE_COLUMNS]
