# ml/mock_odds.py
import random
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database import engine


def ingest_mock() -> pd.DataFrame:
    """
    Restituisce un DataFrame identico a ingest_odds(),
    ma con eventi fittizi realistici.
    """

    with engine.begin() as conn:
        players = conn.execute(
            text("SELECT id, name FROM players ORDER BY random() LIMIT 12")
        ).mappings().all()

    if len(players) < 2:
        print("⚠️ Non abbastanza player per mock odds")
        return pd.DataFrame()

    rows = []
    now = datetime.utcnow()

    for i in range(0, len(players) - 1, 2):
        p1 = players[i]
        p2 = players[i + 1]

        # Odds realistiche
        odds_a = round(random.uniform(1.30, 3.20), 2)
        odds_b = round(random.uniform(1.30, 3.20), 2)

        rows.append({
            "event_id": f"mock_{i}",
            "commence_time": now + timedelta(hours=i),
            "player_a_id": p1["id"],
            "player_b_id": p2["id"],
            "player_a": p1["name"],
            "player_b": p2["name"],
            "odds_player_a": odds_a,
            "odds_player_b": odds_b,
            "surface": random.choice(["hard", "clay", "grass"]),
        })

    df = pd.DataFrame(rows)
    print(f"🧪 Mock odds generate: {len(df)} match")
    return df
