import pandas as pd
from app.database import engine

OUTPUT_PATH = "/data/ml/tennis_dataset.parquet"

def build():
    sql = """
    SELECT
      (fa.elo - fb.elo) AS elo_diff,
      (fa.recent_5 - fb.recent_5) AS recent_5_diff,
      (fa.recent_10 - fb.recent_10) AS recent_10_diff,
      (fa.surface_wr - fb.surface_wr) AS surface_diff,
      (fa.h2h_wins - fb.h2h_wins) AS h2h_diff,
      (fa.rank - fb.rank) AS ranking_diff,
      1 AS target,
      m.match_date

    FROM matches m
    JOIN player_match_features fa
      ON fa.match_id = m.id AND fa.player_id = m.winner_id
    JOIN player_match_features fb
      ON fb.match_id = m.id AND fb.player_id = m.loser_id
    WHERE m.surface IN ('Hard','Clay','Grass')
      AND fa.rank IS NOT NULL AND fb.rank IS NOT NULL
    ORDER BY m.match_date;
    """

    df = pd.read_sql(sql, engine)

    # aggiungo la riga simmetrica (loser come player_A con target 0)
    df_sym = df.copy()
    df_sym["elo_diff"] *= -1
    df_sym["recent_5_diff"] *= -1
    df_sym["recent_10_diff"] *= -1
    df_sym["surface_diff"] *= -1
    df_sym["h2h_diff"] *= -1
    df_sym["ranking_diff"] *= -1
    df_sym["target"] = 0

    dataset = pd.concat([df, df_sym], ignore_index=True)

    dataset.to_parquet(OUTPUT_PATH, index=False)
    print(f"✅ Dataset ML salvato in {OUTPUT_PATH}")
    print(dataset.head())

if __name__ == "__main__":
    build()
