import pandas as pd
from datetime import datetime
from ml.ingest.providers.the_odds_api import fetch_odds

SPORT_KEYS = [
    "tennis_atp_us_open",
    "tennis_atp_wimbledon",
    "tennis_wta_us_open",
]

def ingest() -> pd.DataFrame:
    rows = []

    for sport in SPORT_KEYS:
        events = fetch_odds(sport)
        if not events:
            continue

        for ev in events:
            for bm in ev.get("bookmakers", []):
                market = bm["markets"][0]
                o1, o2 = market["outcomes"]

                rows.append({
                    "event_id": ev["id"],
                    "commence_time": datetime.fromisoformat(
                        ev["commence_time"].replace("Z", "+00:00")
                    ),
                    "player_a": o1["name"],
                    "player_b": o2["name"],
                    "odds_a": o1["price"],
                    "odds_b": o2["price"],
                    "provider": "the_odds_api",
                    "bookmaker": bm["key"]
                })

        if rows:
            break  # fallback stop

    return pd.DataFrame(rows)
