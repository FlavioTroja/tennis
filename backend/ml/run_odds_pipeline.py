"""
Tennis Odds Pipeline
=====================
Pipeline per:
1. Recuperare quote da The Odds API (o mock)
2. Calcolare probabilità col modello ML
3. Trovare value bets
4. Salvare in database

Eseguire con: python -m ml.run_odds_pipeline [--mock]
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import joblib
from sqlalchemy import text

from app.database import engine
from ml.feature_builder import build_features
from ml.edge_engine import evaluate_matches

# Configurazione
MODEL_PATH = Path("/data/ml/models/tennis_model_calibrated.joblib")
FEATURES_PATH = Path("/data/ml/models/feature_columns.json")

MODEL_NAME = "tennis_ml"
MODEL_VERSION = "v2_calibrated"
MIN_EDGE = 0.03  # 3% edge minimo per value bet

# Carica feature list
if FEATURES_PATH.exists():
    with open(FEATURES_PATH) as f:
        FEATURES = json.load(f)
else:
    FEATURES = [
        "elo_diff", "ranking_diff", "recent_5_diff", "recent_10_diff",
        "surface_diff", "h2h_diff"
    ]


def load_model():
    """Carica il modello ML."""
    if not MODEL_PATH.exists():
        print(f"❌ Modello non trovato: {MODEL_PATH}")
        print("   Esegui prima: python -m ml.train_model")
        return None
    
    return joblib.load(MODEL_PATH)


def ensure_value_bets_table():
    """Crea la tabella value_bets se non esiste."""
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS value_bets (
            id SERIAL PRIMARY KEY,
            provider VARCHAR(50),
            bookmaker VARCHAR(50),
            model_name VARCHAR(50),
            model_version VARCHAR(50),
            min_edge_rule FLOAT,
            event_id VARCHAR(100),
            commence_time TIMESTAMP,
            player_a_id INTEGER,
            player_a_name VARCHAR(200),
            player_b_id INTEGER,
            player_b_name VARCHAR(200),
            side VARCHAR(1),
            prob_a FLOAT,
            prob_b FLOAT,
            odds_a FLOAT,
            odds_b FLOAT,
            edge_a FLOAT,
            edge_b FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, bookmaker, model_name)
        )
    """)
    
    with engine.begin() as conn:
        conn.execute(create_sql)


def clear_old_value_bets():
    """Rimuove value bets per eventi già iniziati."""
    with engine.begin() as conn:
        result = conn.execute(text("""
            DELETE FROM value_bets 
            WHERE commence_time < NOW()
            RETURNING id
        """))
        deleted = result.rowcount
        if deleted > 0:
            print(f"🗑️  Rimossi {deleted} eventi passati")


def persist_value_bets(df: pd.DataFrame, provider: str = "the_odds_api"):
    """Salva le value bets nel database."""
    if df.empty:
        return 0
    
    rows = []
    for _, r in df.iterrows():
        # Determina il side consigliato
        if r.get("bet_a", False):
            side = "A"
        elif r.get("bet_b", False):
            side = "B"
        else:
            # Scegli il side con edge maggiore
            side = "A" if r.edge_a > r.edge_b else "B"
        
        # Converti player_id: NaN -> None, float -> int
        player_a_id = None
        player_b_id = None
        
        if pd.notna(r.get("player_a_id")):
            player_a_id = int(r.player_a_id)
        if pd.notna(r.get("player_b_id")):
            player_b_id = int(r.player_b_id)
        
        rows.append({
            "provider": provider,
            "bookmaker": r.get("bookmaker", "unknown"),
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "min_edge_rule": MIN_EDGE,
            "event_id": str(r.event_id),
            "commence_time": r.commence_time,
            "player_a_id": player_a_id,
            "player_a_name": str(r.player_a),
            "player_b_id": player_b_id,
            "player_b_name": str(r.player_b),
            "side": side,
            "prob_a": float(r.prob_a),
            "prob_b": float(r.prob_b),
            "odds_a": float(r.odds_player_a),
            "odds_b": float(r.odds_player_b),
            "edge_a": float(r.edge_a),
            "edge_b": float(r.edge_b),
        })
    
    with engine.begin() as conn:
        # Upsert: aggiorna se esiste, inserisci se nuovo
        for row in rows:
            conn.execute(text("""
                INSERT INTO value_bets (
                    provider, bookmaker, model_name, model_version, min_edge_rule,
                    event_id, commence_time, player_a_id, player_a_name,
                    player_b_id, player_b_name, side, prob_a, prob_b,
                    odds_a, odds_b, edge_a, edge_b
                )
                VALUES (
                    :provider, :bookmaker, :model_name, :model_version, :min_edge_rule,
                    :event_id, :commence_time, :player_a_id, :player_a_name,
                    :player_b_id, :player_b_name, :side, :prob_a, :prob_b,
                    :odds_a, :odds_b, :edge_a, :edge_b
                )
                ON CONFLICT (event_id, bookmaker, model_name) 
                DO UPDATE SET
                    prob_a = EXCLUDED.prob_a,
                    prob_b = EXCLUDED.prob_b,
                    odds_a = EXCLUDED.odds_a,
                    odds_b = EXCLUDED.odds_b,
                    edge_a = EXCLUDED.edge_a,
                    edge_b = EXCLUDED.edge_b,
                    side = EXCLUDED.side,
                    commence_time = EXCLUDED.commence_time
            """), row)
    
    return len(rows)


def run_pipeline(use_mock: bool = False):
    """
    Esegue la pipeline completa.
    
    Args:
        use_mock: Se True, usa dati mock invece di The Odds API
    """
    
    print("=" * 60)
    print(f"🎾 TENNIS ODDS PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 1. Assicura che la tabella esista
    ensure_value_bets_table()
    
    # 2. Pulisci eventi passati
    clear_old_value_bets()
    
    # 3. Carica modello
    model = load_model()
    if model is None:
        return
    
    # 4. Recupera quote
    if use_mock:
        print("\n📊 Modalità: MOCK")
        from ml.mock_odds import ingest_mock
        odds_df = ingest_mock()
        provider = "mock"
    else:
        print("\n📊 Modalità: THE ODDS API (quote reali)")
        from ml.odds_api import ingest_odds
        odds_df = ingest_odds()
        provider = "the_odds_api"
    
    if odds_df.empty:
        print("\n⚠️ Nessun evento disponibile")
        return
    
    print(f"\n📥 Eventi recuperati: {len(odds_df)}")
    
    # 5. Filtra eventi con almeno un player ID
    valid_df = odds_df[
        odds_df["player_a_id"].notna() | odds_df["player_b_id"].notna()
    ].copy()
    
    if valid_df.empty:
        print("⚠️ Nessun evento con giocatori nel database")
        return
    
    print(f"   Eventi con giocatori noti: {len(valid_df)}")
    
    # 6. Calcola feature
    print("\n🔧 Calcolo feature...")
    try:
        features_df = build_features(valid_df)
    except Exception as e:
        print(f"❌ Errore calcolo feature: {e}")
        return
    
    if features_df.empty:
        print("⚠️ Nessuna feature calcolata")
        return
    
    # 7. Predizioni
    print("\n🤖 Calcolo probabilità...")
    
    # Filtra solo le feature disponibili nel modello
    available_features = [f for f in FEATURES if f in features_df.columns]
    
    if not available_features:
        print(f"❌ Nessuna feature disponibile. Richieste: {FEATURES}")
        return
    
    X = features_df[available_features].fillna(0)
    
    try:
        probs = model.predict_proba(X)
        features_df["prob_a"] = probs[:, 1]
        features_df["prob_b"] = probs[:, 0]
    except Exception as e:
        print(f"❌ Errore predizione: {e}")
        return
    
    # 8. Calcola edge
    print("\n📊 Calcolo edge...")
    evaluated = evaluate_matches(features_df)
    
    if evaluated.empty:
        print("⚠️ Nessun match valutato")
        return
    
    # 9. Filtra value bets
    value_bets = evaluated[
        (evaluated.edge_a >= MIN_EDGE) | (evaluated.edge_b >= MIN_EDGE)
    ].copy()
    
    print(f"\n🎯 Value bets trovate: {len(value_bets)} (edge >= {MIN_EDGE*100:.0f}%)")
    
    if value_bets.empty:
        print("   Nessuna value bet al momento")
        return
    
    # 10. Salva nel database
    saved = persist_value_bets(value_bets, provider)
    print(f"💾 Salvate {saved} value bets nel database")
    
    # 11. Log dettagli
    print("\n" + "-" * 60)
    print("📋 DETTAGLI VALUE BETS")
    print("-" * 60)
    
    for _, r in value_bets.iterrows():
        edge = max(r.edge_a, r.edge_b)
        side = "A" if r.edge_a > r.edge_b else "B"
        player = r.player_a if side == "A" else r.player_b
        odds = r.odds_player_a if side == "A" else r.odds_player_b
        prob = r.prob_a if side == "A" else r.prob_b
        
        print(f"  {r.player_a} vs {r.player_b}")
        print(f"    → Bet: {player} @ {odds:.2f}")
        print(f"    → Prob ML: {prob*100:.1f}% | Edge: {edge*100:.1f}%")
        print()


def main():
    """Entry point."""
    # Check se usare mock mode
    use_mock = "--mock" in sys.argv or os.environ.get("USE_MOCK_ODDS", "").lower() == "true"
    
    # Se non c'è API key, usa mock
    if not os.environ.get("ODDS_API_KEY") and not use_mock:
        print("⚠️ ODDS_API_KEY non trovata, uso mock mode")
        use_mock = True
    
    run_pipeline(use_mock=use_mock)


if __name__ == "__main__":
    main()
