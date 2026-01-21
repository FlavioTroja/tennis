"""
The Odds API Client
====================
Recupera quote reali per match di tennis da The Odds API.
https://the-odds-api.com/

Endpoint usati:
- /v4/sports/{sport}/odds - Quote per uno sport
- /v4/sports - Lista sport disponibili

Sport tennis disponibili:
- tennis_atp_aus_open_singles
- tennis_atp_french_open
- tennis_atp_us_open  
- tennis_atp_wimbledon
- tennis_wta_aus_open_singles
- etc.
"""

import os
from datetime import datetime
from typing import Optional
import requests
import pandas as pd
from sqlalchemy import text
from app.database import engine

# API Configuration
API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"

# Sport keys per tennis ATP
TENNIS_SPORTS = [
    "tennis_atp_aus_open_singles",
    "tennis_atp_french_open",
    "tennis_atp_us_open",
    "tennis_atp_wimbledon",
    "tennis_atp_indian_wells",
    "tennis_atp_miami_open",
    "tennis_atp_monte_carlo",
    "tennis_atp_madrid_open",
    "tennis_atp_rome",
    "tennis_atp_canadian_open",
    "tennis_atp_cincinnati",
    "tennis_atp_shanghai",
    "tennis_atp_paris",
    "tennis_atp_finals",
    # WTA
    "tennis_wta_aus_open_singles",
    "tennis_wta_french_open",
    "tennis_wta_us_open",
    "tennis_wta_wimbledon",
]

# Bookmakers preferiti (in ordine di preferenza)
PREFERRED_BOOKMAKERS = [
    "pinnacle",
    "betfair_ex_eu",
    "betfair",
    "bet365",
    "unibet_eu",
    "williamhill",
]

# Mapping superficie per torneo
TOURNAMENT_SURFACES = {
    "aus_open": "Hard",
    "french_open": "Clay",
    "us_open": "Hard",
    "wimbledon": "Grass",
    "indian_wells": "Hard",
    "miami": "Hard",
    "monte_carlo": "Clay",
    "madrid": "Clay",
    "rome": "Clay",
    "canadian": "Hard",
    "cincinnati": "Hard",
    "shanghai": "Hard",
    "paris": "Hard",
    "finals": "Hard",
}


def get_surface_from_sport(sport_key: str) -> str:
    """Determina la superficie dal nome del torneo."""
    sport_lower = sport_key.lower()
    for tournament, surface in TOURNAMENT_SURFACES.items():
        if tournament in sport_lower:
            return surface
    return "Hard"  # Default


def get_available_sports() -> list:
    """Ritorna la lista di sport disponibili con eventi attivi."""
    if not API_KEY:
        print("⚠️ ODDS_API_KEY non configurata")
        return []
    
    try:
        resp = requests.get(
            f"{BASE_URL}/sports",
            params={"apiKey": API_KEY},
            timeout=10
        )
        resp.raise_for_status()
        
        sports = resp.json()
        tennis_sports = [s for s in sports if s["key"].startswith("tennis_")]
        
        print(f"🎾 Sport tennis disponibili: {len(tennis_sports)}")
        for s in tennis_sports:
            if s.get("active"):
                print(f"   ✅ {s['key']} - {s['title']}")
        
        return [s["key"] for s in tennis_sports if s.get("active")]
        
    except Exception as e:
        print(f"❌ Errore get_available_sports: {e}")
        return []


def fetch_odds_for_sport(sport_key: str, regions: str = "eu,uk") -> list:
    """
    Recupera le quote per uno sport specifico.
    
    Args:
        sport_key: es. "tennis_atp_aus_open_singles"
        regions: Regioni bookmaker (eu, uk, us, au)
    
    Returns:
        Lista di eventi con quote
    """
    if not API_KEY:
        return []
    
    try:
        resp = requests.get(
            f"{BASE_URL}/sports/{sport_key}/odds",
            params={
                "apiKey": API_KEY,
                "regions": regions,
                "markets": "h2h",  # Head to head (moneyline)
                "oddsFormat": "decimal",
            },
            timeout=15
        )
        
        # Check API usage
        remaining = resp.headers.get("x-requests-remaining", "?")
        used = resp.headers.get("x-requests-used", "?")
        print(f"   API calls: {used} used, {remaining} remaining")
        
        resp.raise_for_status()
        return resp.json()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ API key invalida o scaduta")
        elif e.response.status_code == 429:
            print("❌ Rate limit raggiunto")
        else:
            print(f"❌ HTTP Error: {e}")
        return []
    except Exception as e:
        print(f"❌ Errore fetch_odds: {e}")
        return []


def get_best_odds(bookmakers: list) -> tuple:
    """
    Estrae le migliori quote dai bookmaker disponibili.
    
    Returns:
        (odds_a, odds_b, bookmaker_name) o (None, None, None)
    """
    if not bookmakers:
        return None, None, None
    
    # Cerca nei bookmaker preferiti prima
    for preferred in PREFERRED_BOOKMAKERS:
        for bm in bookmakers:
            if bm["key"] == preferred:
                for market in bm.get("markets", []):
                    if market["key"] == "h2h":
                        outcomes = market.get("outcomes", [])
                        if len(outcomes) >= 2:
                            odds_a = outcomes[0]["price"]
                            odds_b = outcomes[1]["price"]
                            return odds_a, odds_b, bm["key"]
    
    # Fallback: primo bookmaker disponibile
    for bm in bookmakers:
        for market in bm.get("markets", []):
            if market["key"] == "h2h":
                outcomes = market.get("outcomes", [])
                if len(outcomes) >= 2:
                    odds_a = outcomes[0]["price"]
                    odds_b = outcomes[1]["price"]
                    return odds_a, odds_b, bm["key"]
    
    return None, None, None


def normalize_player_name(name: str) -> str:
    """
    Normalizza il nome del giocatore per il matching con il DB.
    The Odds API usa formati come "Novak Djokovic" o "N. Djokovic".
    """
    # Rimuovi punti e normalizza spazi
    name = name.replace(".", "").strip()
    
    # Espandi iniziali comuni (opzionale, per matching migliore)
    # es. "N Djokovic" -> cerca pattern
    
    return name


def find_player_id(player_name: str) -> Optional[int]:
    """Cerca l'ID del giocatore nel database."""
    normalized = normalize_player_name(player_name)
    
    # Prova match esatto
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM players WHERE name = :name"),
            {"name": normalized}
        ).scalar()
        
        if result:
            return int(result)
        
        # Prova match parziale (cognome)
        parts = normalized.split()
        if len(parts) >= 2:
            lastname = parts[-1]
            result = conn.execute(
                text("SELECT id FROM players WHERE name ILIKE :pattern ORDER BY id DESC LIMIT 1"),
                {"pattern": f"%{lastname}"}
            ).scalar()
            
            if result:
                return int(result)
    
    return None


def ingest_odds() -> pd.DataFrame:
    """
    Recupera quote reali da The Odds API per tutti i tornei tennis attivi.
    
    Returns:
        DataFrame con colonne:
        - event_id, commence_time, sport_key
        - player_a, player_b, player_a_id, player_b_id
        - odds_player_a, odds_player_b, bookmaker
        - surface
    """
    
    print("=" * 60)
    print("🎾 THE ODDS API - Recupero quote tennis")
    print("=" * 60)
    
    if not API_KEY:
        print("❌ ODDS_API_KEY non configurata!")
        print("   Aggiungi la variabile d'ambiente o usa il mock mode")
        return pd.DataFrame()
    
    # Trova sport attivi
    active_sports = get_available_sports()
    
    if not active_sports:
        print("⚠️ Nessun torneo tennis attivo al momento")
        return pd.DataFrame()
    
    all_events = []
    
    for sport_key in active_sports:
        print(f"\n📡 Fetching: {sport_key}")
        events = fetch_odds_for_sport(sport_key)
        
        surface = get_surface_from_sport(sport_key)
        
        for event in events:
            odds_a, odds_b, bookmaker = get_best_odds(event.get("bookmakers", []))
            
            if odds_a is None or odds_b is None:
                continue
            
            # Player names dall'API
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")
            
            # Cerca ID nel DB
            player_a_id = find_player_id(home_team)
            player_b_id = find_player_id(away_team)
            
            # Skip se non troviamo almeno un giocatore
            if player_a_id is None and player_b_id is None:
                print(f"   ⚠️ Skip: {home_team} vs {away_team} (giocatori non trovati)")
                continue
            
            all_events.append({
                "event_id": event["id"],
                "commence_time": datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00")),
                "sport_key": sport_key,
                "player_a": home_team,
                "player_b": away_team,
                "player_a_id": player_a_id,
                "player_b_id": player_b_id,
                "odds_player_a": odds_a,
                "odds_player_b": odds_b,
                "bookmaker": bookmaker,
                "surface": surface,
            })
    
    df = pd.DataFrame(all_events)
    
    print(f"\n✅ Totale eventi recuperati: {len(df)}")
    if not df.empty:
        print(f"   Con ID giocatore: {df['player_a_id'].notna().sum()}")
    
    return df


def check_api_status():
    """Verifica lo stato dell'API e i crediti rimanenti."""
    if not API_KEY:
        print("❌ ODDS_API_KEY non configurata")
        return
    
    try:
        resp = requests.get(
            f"{BASE_URL}/sports",
            params={"apiKey": API_KEY},
            timeout=10
        )
        
        print("📊 The Odds API Status:")
        print(f"   Requests used: {resp.headers.get('x-requests-used', '?')}")
        print(f"   Requests remaining: {resp.headers.get('x-requests-remaining', '?')}")
        print(f"   Status: {'✅ OK' if resp.status_code == 200 else '❌ Error'}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


if __name__ == "__main__":
    # Test
    check_api_status()
    print()
    df = ingest_odds()
    if not df.empty:
        print("\nPrimi 5 eventi:")
        print(df.head())
