import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = "/data/ml/tennis_model.joblib"


def temporal_split(df):
    train = df[df.match_date <= "2021-12-31"]
    val = df[(df.match_date > "2021-12-31") & (df.match_date <= "2022-12-31")]
    test = df[df.match_date > "2022-12-31"]
    return train, val, test


def train():
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])

    features = ["elo_diff"]

    train_df, val_df, test_df = temporal_split(df)

    X_train = train_df[features]
    y_train = train_df["target"]

    X_val = val_df[features]
    y_val = val_df["target"]

    X_test = test_df[features]
    y_test = test_df["target"]

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000))
    ])

    pipeline.fit(X_train, y_train)

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
