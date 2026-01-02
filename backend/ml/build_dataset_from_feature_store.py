import pandas as pd
from sqlalchemy import text
from app.database import engine

OUTPUT_PATH = "/data/ml/tennis_dataset.parquet"
BASE_ELO = 1500.0

# ==========================================================
# Recupero Elo PRE-match (per superficie)
# ==========================================================

ELO_SQL = """
SELECT pe.elo
FROM player_elo pe
WHERE pe.player_id = :pid
  AND pe.surface = :surface
  AND pe.match_id < :mid
ORDER BY pe.match_id DESC
LIMIT 1;
"""


def get_elo(pid: int, surface: str, match_id: int) -> float:
    with engine.connect() as conn:
        v = conn.execute(
            text(ELO_SQL),
            {"pid": pid, "surface": surface, "mid": match_id}
        ).scalar()
    return float(v) if v is not None else BASE_ELO


# ==========================================================
# Dataset builder (Elo-only)
# ==========================================================

def build_dataset():
    matches_sql = """
    SELECT
        id,
        match_date,
        surface,
        winner_id,
        loser_id
    FROM matches
    WHERE surface IS NOT NULL
    ORDER BY match_date ASC, id ASC;
    """

    df = pd.read_sql(matches_sql, engine)
    df["match_date"] = pd.to_datetime(df["match_date"]).dt.date

    rows = []

    for _, m in df.iterrows():
        surface = m.surface
        if surface not in ("Hard", "Clay", "Grass"):
            continue

        mid = int(m.id)
        date = m.match_date

        A = int(m.winner_id)
        B = int(m.loser_id)

        elo_A = get_elo(A, surface, mid)
        elo_B = get_elo(B, surface, mid)

        # A vince
        rows.append({
            "elo_diff": elo_A - elo_B,
            "target": 1,
            "match_date": date
        })

        # B perde (simmetrica)
        rows.append({
            "elo_diff": elo_B - elo_A,
            "target": 0,
            "match_date": date
        })

    dataset = pd.DataFrame(rows)
    dataset.to_parquet(OUTPUT_PATH, index=False)

    print(f"✅ Dataset ML Elo-only salvato in {OUTPUT_PATH}")
    print(dataset.head())


if __name__ == "__main__":
    build_dataset()
