import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import (
    roc_auc_score,
    log_loss,
    brier_score_loss
)
from sklearn.calibration import calibration_curve

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = "/data/ml/tennis_model.joblib"


def backtest():
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])

    test_df = df[df.match_date > "2022-12-31"]

    features = [
        "elo_diff",
        "ranking_diff",
        "recent_5_diff",
        "recent_10_diff",
        "surface_diff",
        "h2h_diff",
    ]

    X = test_df[features]
    y = test_df["target"]

    model = joblib.load(MODEL_PATH)
    probs = model.predict_proba(X)[:, 1]

    print("\n📊 BACKTEST METRICHE (TEST SET)\n")
    print(f"ROC-AUC     : {roc_auc_score(y, probs):.3f}")
    print(f"LogLoss     : {log_loss(y, probs):.3f}")
    print(f"Brier Score : {brier_score_loss(y, probs):.3f}")

    # ---------- CALIBRATION ----------
    frac_pos, mean_pred = calibration_curve(
        y, probs, n_bins=10, strategy="uniform"
    )

    calib = pd.DataFrame({
        "mean_predicted_prob": mean_pred,
        "observed_win_rate": frac_pos,
        "gap": frac_pos - mean_pred
    })

    print("\n📐 CALIBRATION TABLE\n")
    print(calib.round(3))

    # ---------- EDGE SIMULATION ----------
    test_df = test_df.copy()
    test_df["prob"] = probs
    test_df["prediction"] = (probs > 0.5).astype(int)
    test_df["correct"] = test_df["prediction"] == test_df["target"]

    accuracy = test_df["correct"].mean()

    print("\n🎯 DECISION METRICHE\n")
    print(f"Decision Accuracy (>0.5): {accuracy:.3f}")

    # ---------- FAIR ODDS SIMULATION ----------
    test_df["fair_odds"] = 1 / test_df["prob"].clip(0.01, 0.99)
    test_df["roi"] = np.where(
        test_df["correct"],
        test_df["fair_odds"] - 1,
        -1
    )

    roi = test_df["roi"].mean()

    print("\n💰 FAIR-ODDS ROI SIMULATION\n")
    print(f"Avg ROI per bet: {roi:.3f}")


if __name__ == "__main__":
    backtest()
