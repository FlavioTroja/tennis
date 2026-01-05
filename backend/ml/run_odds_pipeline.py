# ml/run_odds_pipeline.py
import joblib
from ml.edge_engine import evaluate_matches
from ml.feature_builder import build_features
from ml.mock_odds import ingest_mock

MODEL_PATH = "/data/ml/tennis_model_calibrated.joblib"
FEATURES = ["elo_diff"]

model = joblib.load(MODEL_PATH)


def main():
    print("▶️ Avvio pipeline odds (MOCK MODE)")

    odds_df = ingest_mock()
    if odds_df.empty:
        print("⚠️ Nessuna odds disponibile")
        return

    features_df = build_features(odds_df)

    X = features_df[FEATURES]
    probs = model.predict_proba(X)

    features_df["prob_a"] = probs[:, 1]
    features_df["prob_b"] = probs[:, 0]

    evaluated = evaluate_matches(features_df)

    value_bets = evaluated[
        evaluated.bet_a | evaluated.bet_b
    ].copy()

    print(f"🎯 Value bets trovate: {len(value_bets)}")

    # LOG (il DB lo collegheremo dopo)
    for _, r in value_bets.iterrows():
        side = "A" if r.bet_a else "B"
        edge = r.edge_a if r.bet_a else r.edge_b
        print(
            f"✅ {r.player_a} vs {r.player_b} | side={side} | edge={edge:.3f}"
        )


if __name__ == "__main__":
    main()
