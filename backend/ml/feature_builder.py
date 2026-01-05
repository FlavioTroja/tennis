import pandas as pd
from sqlalchemy import text
from app.database import engine

DEFAULT_ELO = 1500.0


def get_latest_surface_elo(player_id: int, surface: str, date) -> float:
    """
    Ritorna l'ultimo Elo per giocatore+superficie.
    Se la tabella non esiste o non ci sono record → DEFAULT_ELO.
    """
    q = text("""
        SELECT elo
        FROM player_elo_surface
        WHERE player_id = :pid
          AND surface = :surface
          AND match_date < :date
        ORDER BY match_date DESC
        LIMIT 1
    """)

    try:
        with engine.begin() as conn:
            r = conn.execute(
                q,
                {
                    "pid": player_id,
                    "surface": surface,
                    "date": date,
                }
            ).scalar()

        return float(r) if r is not None else DEFAULT_ELO

    except Exception:
        # 🔥 fallback fondamentale:
        # - tabella non ancora creata
        # - bootstrap / mock mode
        return DEFAULT_ELO


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input REQUIRED columns:
    - player_a_id
    - player_b_id
    - surface
    - commence_time
    """

    rows = []

    for _, r in df.iterrows():
        elo_a = get_latest_surface_elo(
            r.player_a_id,
            r.surface,
            r.commence_time
        )
        elo_b = get_latest_surface_elo(
            r.player_b_id,
            r.surface,
            r.commence_time
        )

        rows.append({
            **r.to_dict(),
            "elo_diff": elo_a - elo_b
        })

    return pd.DataFrame(rows)
