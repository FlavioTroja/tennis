import pandas as pd
import numpy as np
import joblib

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = "/data/ml/tennis_model.joblib"

BOOK_MARGIN = 0.93     # 7% bookmaker margin
EDGE_THRESHOLD = 0.0  # bet only if edge > 0

FEATURES = ["elo_diff"]

def simulate():
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])

    # Test set
    test_df = df[df.match_date > "2022-12-31"].copy()

    X = test_df[FEATURES]
    y = test_df["target"]

    model = joblib.load(MODEL_PATH)
    probs = model.predict_proba(X)[:, 1]

    # --- Bookmaker simulation ---
    test_df["model_prob"] = probs
    test_df["fair_odds"] = 1 / test_df["model_prob"].clip(0.01, 0.99)
    test_df["book_odds"] = test_df["fair_odds"] * BOOK_MARGIN
    test_df["implied_prob"] = 1 / test_df["book_odds"]

    test_df["edge"] = test_df["model_prob"] - test_df["implied_prob"]

    # Bet only with positive edge
    bets = test_df[test_df["edge"] > EDGE_THRESHOLD].copy()

    bets["win"] = bets["target"] == 1
    bets["roi"] = np.where(
        bets["win"],
        bets["book_odds"] - 1,
        -1
    )

    # --- Metrics ---
    print("\n💰 BOOKMAKER SIMULATION RESULTS\n")
    print(f"Bets placed        : {len(bets)}")
    print(f"Hit rate           : {bets['win'].mean():.3f}")
    print(f"Avg ROI per bet    : {bets['roi'].mean():.3f}")
    print(f"Total ROI (sum)    : {bets['roi'].sum():.2f}")
    print(f"Avg edge           : {bets['edge'].mean():.4f}")


if __name__ == "__main__":
    simulate()
