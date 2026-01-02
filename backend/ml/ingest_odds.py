import os
import requests
import pandas as pd
from datetime import datetime
from sqlalchemy import text

from app.database import engine

API_KEY = os.getenv("ODDS_API_KEY")

# Endpoint base: tennis (competition-agnostic)
BASE_URL = "https://api.the-odds-api.com/v4/sports/tennis/odds"

BOOKMAKERS = ["bet365", "unibet", "williamhill"]
REGIONS = "eu"
MARKETS = "h2h"


def ingest() -> pd.DataFrame:
    """
    Ingest odds da The Odds API.
    - Inserisce snapshot nel DB
    - Ritorna un DataFrame con le odds correnti
    """

    if not API_KEY:
        raise RuntimeError("ODDS_API_KEY non impostata")

    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal",
        "bookmakers": ",".join(BOOKMAKERS),
    }

    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()

    events = resp.json()
    rows: list[dict] = []

    for ev in events:
        event_id = ev["id"]
        commence_time = datetime.fromisoformat(
            ev["commence_time"].replace("Z", "+00:00")
        )

        home = ev["home_team"]
        away = ev["away_team"]

        for bm in ev.get("bookmakers", []):
            bookmaker = bm["key"]

            markets = bm.get("markets", [])
            if not markets:
                continue

            market = markets[0]  # h2h
            outcomes = market.get("outcomes", [])
            if len(outcomes) != 2:
                continue

            o1, o2 = outcomes
            odds_map = {
                o1["name"]: o1["price"],
                o2["name"]: o2["price"],
            }

            if home not in odds_map or away not in odds_map:
                continue

            rows.append({
                "provider": "the_odds_api",
                "bookmaker": bookmaker,
                "event_id": event_id,
                "commence_time": commence_time,
                "player_a": home,
                "player_b": away,
                "odds_a": odds_map[home],
                "odds_b": odds_map[away],
            })

    # 🔑 SEMPRE restituire un DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        print("⚠️ Nessuna odds trovata")
        return df

    # Persistenza DB (snapshot idempotente)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO odds_snapshots
                    (provider, bookmaker, event_id, commence_time,
                     player_a, player_b, odds_a, odds_b)
                VALUES
                    (:provider, :bookmaker, :event_id, :commence_time,
                     :player_a, :player_b, :odds_a, :odds_b)
                ON CONFLICT DO NOTHING
            """),
            df.to_dict(orient="records")
        )

    print(f"✅ Inserite {len(df)} odds snapshot")
    return df


if __name__ == "__main__":
    ingest()
