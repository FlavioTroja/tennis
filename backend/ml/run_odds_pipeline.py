import pandas as pd
import joblib

from ml.ingest_odds import ingest
from ml.edge_engine import evaluate_matches
from ml.feature_builder import build_features  # FUTURO

MODEL_PATH = "/data/ml/tennis_model_calibrated.joblib"
FEATURES = ["elo_diff"]

model = joblib.load(MODEL_PATH)


def main():
    odds_df = ingest()

    features_df = build_features(odds_df)

    X = features_df[["elo_diff"]]
    probs = model.predict_proba(X)

    features_df["prob_a"] = probs[:, 1]
    features_df["prob_b"] = probs[:, 0]

    evaluated = evaluate_matches(features_df)

    value_bets = evaluated[
        evaluated.bet_a | evaluated.bet_b
    ]

    print(f"🎯 Value bets trovate: {len(value_bets)}")

    for _, r in value_bets.iterrows():
        side = "A" if r.bet_a else "B"
        edge = r.edge_a if r.bet_a else r.edge_b
        print(
            f"✅ {r.player_a} vs {r.player_b} | side={side} | edge={edge:.3f}"
        )
