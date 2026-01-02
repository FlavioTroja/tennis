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

    # ---- TEST SET TEMPORALE ----
    test_df = df[df.match_date > "2022-12-31"].copy()

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

    # ---------- METRICHE CLASSICHE ----------
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

    # ---------- DECISION METRIC ----------
    test_df["prob"] = probs
    test_df["prediction"] = (probs > 0.5).astype(int)
    test_df["correct"] = test_df["prediction"] == test_df["target"]

    accuracy = test_df["correct"].mean()

    print("\n🎯 DECISION METRICHE\n")
    print(f"Decision Accuracy (>0.5): {accuracy:.3f}")

    # ==========================================================
    # 🎯 BETTING SIMULATION (CORRETTA)
    # ==========================================================

    # ---- Simulazione bookmaker (margine 5%) ----
    margin = 0.05
    test_df["book_odds"] = 1 / (test_df["prob"] * (1 - margin))

    # ---- Edge ----
    test_df["edge"] = test_df["prob"] - (1 / test_df["book_odds"])

    # ---- Bet solo se edge > soglia ----
    EDGE_THRESHOLD = 0.03
    bets = test_df[test_df["edge"] > EDGE_THRESHOLD].copy()

    if bets.empty:
        print("\n💰 BETTING SIMULATION\n")
        print("Nessuna bet piazzata (edge troppo basso)")
        return

    bets["roi"] = np.where(
        bets["target"] == 1,
        bets["book_odds"] - 1,
        -1
    )

    print("\n💰 BETTING SIMULATION (EDGE FILTERED)\n")
    print(f"Bets piazzate        : {len(bets)}")
    print(f"Avg ROI per bet      : {bets['roi'].mean():.3f}")
    print(f"Total ROI (somma)    : {bets['roi'].sum():.2f}")
    print(f"Hit rate             : {(bets['roi'] > 0).mean():.3f}")


if __name__ == "__main__":
    backtest()
