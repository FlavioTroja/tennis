from ml.ingest_odds import ingest
from ml.edge_engine import evaluate_matches
from ml.feature_pipeline import (
    compute_features_df,
    get_feature_matrix,
)

import joblib

MODEL_PATH = "/data/ml/tennis_model.joblib"
model = joblib.load(MODEL_PATH)


def add_predictions(df):
    X = get_feature_matrix(df)
    probs = model.predict_proba(X)

    df = df.copy()
    df["prob_a"] = probs[:, 1]
    df["prob_b"] = probs[:, 0]
    return df


def main():
    odds_df = ingest()

    if odds_df is None or odds_df.empty:
        print("⚠️ Nessuna odds disponibile")
        return

    odds_df = compute_features_df(odds_df)
    odds_df = add_predictions(odds_df)
    odds_df = evaluate_matches(odds_df)

    value_bets = odds_df[
        odds_df.bet_a | odds_df.bet_b
    ]

    print(f"\n🎯 Value bets trovate: {len(value_bets)}\n")

    for _, r in value_bets.iterrows():
        side = "A" if r.bet_a else "B"
        edge = r.edge_a if r.bet_a else r.edge_b
        prob = r.prob_a if side == "A" else r.prob_b

        print(
            f"{r.player_a} vs {r.player_b} | "
            f"side={side} | prob={prob:.3f} | edge={edge:.3f}"
        )


if __name__ == "__main__":
    main()
