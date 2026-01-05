import pandas as pd
import joblib
from sqlalchemy import text

from app.database import engine
from ml.ingest_odds import ingest
from ml.edge_engine import evaluate_matches
from ml.feature_builder import build_features  # FUTURO

MODEL_PATH = "/data/ml/tennis_model_calibrated.joblib"
FEATURES = ["elo_diff"]

model = joblib.load(MODEL_PATH)


def store_value_bets(df: pd.DataFrame):
    """
    Scrive/aggiorna la tabella value_bets.
    Richiede colonne:
    - event_id
    - commence_time
    - player_a_id
    - player_b_id
    - prob_a, prob_b
    - odds_a, odds_b
    - edge_a, edge_b
    """

    if df.empty:
        return

    rows = df[
        [
            "event_id",
            "commence_time",
            "player_a_id",
            "player_b_id",
            "prob_a",
            "prob_b",
            "odds_a",
            "odds_b",
            "edge_a",
            "edge_b",
        ]
    ].to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO value_bets (
                    event_id,
                    commence_time,
                    player_a_id,
                    player_b_id,
                    prob_a,
                    prob_b,
                    odds_a,
                    odds_b,
                    edge_a,
                    edge_b
                )
                VALUES (
                    :event_id,
                    :commence_time,
                    :player_a_id,
                    :player_b_id,
                    :prob_a,
                    :prob_b,
                    :odds_a,
                    :odds_b,
                    :edge_a,
                    :edge_b
                )
                ON CONFLICT (event_id) DO UPDATE SET
                    prob_a = EXCLUDED.prob_a,
                    prob_b = EXCLUDED.prob_b,
                    odds_a = EXCLUDED.odds_a,
                    odds_b = EXCLUDED.odds_b,
                    edge_a = EXCLUDED.edge_a,
                    edge_b = EXCLUDED.edge_b,
                    updated_at = NOW()
            """),
            rows
        )


def main():
    # 1. Ingest odds
    odds_df = ingest()
    if odds_df.empty:
        print("⚠️ Nessuna odds disponibile")
        return

    # 2. Feature engineering
    features_df = build_features(odds_df)

    # 3. Predict probabilities (multi-feature ready)
    X = features_df[FEATURES]
    probs = model.predict_proba(X)

    features_df["prob_a"] = probs[:, 1]
    features_df["prob_b"] = probs[:, 0]

    # 4. Edge + bet decision
    evaluated = evaluate_matches(features_df)

    value_bets = evaluated[
        evaluated.bet_a | evaluated.bet_b
    ].copy()

    print(f"🎯 Value bets trovate: {len(value_bets)}")

    # 5. Persistenza DB (QUESTO ERA IL PEZZO MANCANTE)
    store_value_bets(value_bets)

    # 6. Log diagnostico
    for _, r in value_bets.iterrows():
        side = "A" if r.bet_a else "B"
        edge = r.edge_a if r.bet_a else r.edge_b
        print(
            f"✅ {r.player_a} vs {r.player_b} | side={side} | edge={edge:.3f}"
        )


if __name__ == "__main__":
    main()
