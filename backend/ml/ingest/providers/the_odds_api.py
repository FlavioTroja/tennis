import os
import requests

API_KEY = os.getenv("ODDS_API_KEY")

def fetch_odds(sport_key: str) -> list[dict]:
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    r = requests.get(url, params=params, timeout=20)
    if r.status_code != 200:
        return []

    return r.json()
