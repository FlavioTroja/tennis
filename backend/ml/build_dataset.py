import pandas as pd
from sqlalchemy import text
from app.database import engine

OUTPUT_PATH = "/data/ml/tennis_dataset.parquet"


# ---------- QUERY FEATURE SQL ----------

RECENT_N_SQL = """
SELECT AVG(win) FROM (
    SELECT win
    FROM player_matches
    WHERE player_id = :pid
      AND match_date < :date
    ORDER BY match_date DESC
    LIMIT :n
) t;
"""

SURFACE_SQL = """
SELECT AVG(win)
FROM player_matches
WHERE player_id = :pid
  AND surface = :surface
  AND match_date < :date;
"""

H2H_SQL = """
SELECT COUNT(*)
FROM player_matches
WHERE player_id = :a
  AND opponent_id = :b
  AND win = 1
  AND match_date < :date;
"""


# ---------- FEATURE FUNCTIONS ----------

def scalar(query, params):
    with engine.connect() as conn:
        value = conn.execute(text(query), params).scalar()
        if value is None:
            return 0.0
        return float(value)



def recent_winrate(pid, date, n):
    return scalar(RECENT_N_SQL, {"pid": pid, "date": date, "n": n})


def surface_winrate(pid, surface, date):
    return scalar(SURFACE_SQL, {"pid": pid, "surface": surface, "date": date})


def h2h_wins(a, b, date):
    return scalar(H2H_SQL, {"a": a, "b": b, "date": date})


# ---------- DATASET BUILDER ----------

def build_dataset():
    matches_sql = """
    SELECT
        id,
        match_date,
        surface,
        winner_id,
        loser_id,
        winner_rank,
        loser_rank
    FROM matches
    WHERE winner_rank IS NOT NULL
      AND loser_rank IS NOT NULL
    ORDER BY match_date;
    """

    df = pd.read_sql(matches_sql, engine)

    rows = []

    for _, m in df.iterrows():
        date = m.match_date
        surface = m.surface

        A = m.winner_id
        B = m.loser_id

        # Feature giocatore A
        A_r5 = recent_winrate(A, date, 5)
        A_r10 = recent_winrate(A, date, 10)
        A_surf = surface_winrate(A, surface, date)
        A_h2h = h2h_wins(A, B, date)

        # Feature giocatore B
        B_r5 = recent_winrate(B, date, 5)
        B_r10 = recent_winrate(B, date, 10)
        B_surf = surface_winrate(B, surface, date)
        B_h2h = h2h_wins(B, A, date)

        # Riga 1: A vince
        rows.append({
            "ranking_diff": m.winner_rank - m.loser_rank,
            "recent_5_diff": A_r5 - B_r5,
            "recent_10_diff": A_r10 - B_r10,
            "surface_diff": A_surf - B_surf,
            "h2h_diff": A_h2h - B_h2h,
            "target": 1,
            "match_date": date
        })

        # Riga 2: B perde (simmetrica)
        rows.append({
            "ranking_diff": m.loser_rank - m.winner_rank,
            "recent_5_diff": B_r5 - A_r5,
            "recent_10_diff": B_r10 - A_r10,
            "surface_diff": B_surf - A_surf,
            "h2h_diff": B_h2h - A_h2h,
            "target": 0,
            "match_date": date
        })

    dataset = pd.DataFrame(rows)
    dataset.to_parquet(OUTPUT_PATH, index=False)
    print(f"✅ Dataset ML salvato in {OUTPUT_PATH}")
    print(dataset.head())


if __name__ == "__main__":
    build_dataset()
