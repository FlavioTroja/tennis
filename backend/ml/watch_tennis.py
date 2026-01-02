import requests
import os

API_KEY = os.getenv("ODDS_API_KEY")
SPORTS_URL = "https://api.the-odds-api.com/v4/sports"

def is_tennis_active():
    resp = requests.get(SPORTS_URL, params={
        "all": "true",
        "apiKey": API_KEY
    })
    resp.raise_for_status()

    sports = resp.json()

    tennis = [
        s for s in sports
        if s["key"].startswith("tennis_") and s["active"]
    ]

    return tennis


if __name__ == "__main__":
    active = is_tennis_active()

    if not active:
        print("⏳ Nessun torneo tennis attivo")
    else:
        print("🎾 Tennis attivo:")
        for s in active:
            print(f"- {s['key']} ({s['title']})")
