import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = "/data/ml/tennis_model.joblib"


def temporal_split(df):
    cutoff_train = pd.Timestamp("2021-12-31")
    cutoff_val = pd.Timestamp("2022-12-31")

    train = df[df.match_date <= cutoff_train]
    val = df[(df.match_date > cutoff_train) & (df.match_date <= cutoff_val)]
    test = df[df.match_date > cutoff_val]

    return train, val, test


def train():
    # --- Load dataset ---
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])

    # --- Feature set (production-grade) ---
    features = [
        "elo_diff",
        "ranking_diff",
        "recent_5_diff",
        "recent_10_diff",
        "surface_diff",
        "h2h_diff",
    ]

    # Safety check
    missing = set(features) - set(df.columns)
    if missing:
        raise ValueError(f"❌ Feature mancanti nel dataset: {missing}")

    train_df, val_df, test_df = temporal_split(df)

    X_train = train_df[features]
    y_train = train_df["target"]

    X_val = val_df[features]
    y_val = val_df["target"]

    X_test = test_df[features]
    y_test = test_df["target"]

    # --- Model pipeline ---
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=2000,
            solver="lbfgs",
            n_jobs=-1
        ))
    ])

    pipeline.fit(X_train, y_train)

    # --- Evaluation ---
    val_pred = pipeline.predict_proba(X_val)[:, 1]
    test_pred = pipeline.predict_proba(X_test)[:, 1]

    print("\n📊 METRICHE")
    print(f"Validation ROC-AUC: {roc_auc_score(y_val, val_pred):.3f}")
    print(f"Validation LogLoss: {log_loss(y_val, val_pred):.3f}")
    print(f"Test ROC-AUC: {roc_auc_score(y_test, test_pred):.3f}")
    print(f"Test LogLoss: {log_loss(y_test, test_pred):.3f}")

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\n✅ Modello salvato in {MODEL_PATH}")


if __name__ == "__main__":
    train()
