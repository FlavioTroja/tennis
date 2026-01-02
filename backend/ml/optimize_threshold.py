import pandas as pd
import numpy as np
import joblib

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = "/data/ml/tennis_model.joblib"


def optimize():
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])

    test_df = df[df.match_date > "2022-12-31"].copy()

    features = ["elo_diff"]
    X = test_df[features]
    y = test_df["target"]

    model = joblib.load(MODEL_PATH)
    probs = model.predict_proba(X)[:, 1]

    test_df["prob"] = probs
    test_df["correct"] = test_df["target"] == 1

    results = []

    for threshold in np.arange(0.50, 0.90, 0.02):
        bets = test_df[test_df["prob"] >= threshold]

        if len(bets) < 200:
            continue  # evita overfitting

        bets = bets.copy()
        bets["fair_odds"] = 1 / bets["prob"]
        bets["roi"] = np.where(
            bets["correct"],
            bets["fair_odds"] - 1,
            -1
        )

        results.append({
            "threshold": round(threshold, 2),
            "bets": len(bets),
            "hit_rate": bets["correct"].mean(),
            "avg_roi": bets["roi"].mean(),
            "total_roi": bets["roi"].sum(),
        })

    res = pd.DataFrame(results).sort_values(
        "total_roi", ascending=False
    )

    print("\n📊 THRESHOLD OPTIMIZATION RESULTS\n")
    print(res.head(10).round(3))


if __name__ == "__main__":
    optimize()
