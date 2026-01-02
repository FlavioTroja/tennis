import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = "/data/ml/tennis_model_calibrated.joblib"

FEATURES = ["elo_diff"]


def train():
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])

    # split temporale (no leakage)
    train_df = df[df.match_date <= "2022-12-31"]
    test_df = df[df.match_date > "2022-12-31"]

    X_train = train_df[FEATURES]
    y_train = train_df["target"]

    # modello base
    base_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(max_iter=1000))
    ])

    # calibrazione
    calibrated_model = CalibratedClassifierCV(
        estimator=base_pipeline,
        method="sigmoid",
        cv=5
    )

    calibrated_model.fit(X_train, y_train)

    joblib.dump(calibrated_model, MODEL_PATH)
    print(f"✅ Modello calibrato salvato in {MODEL_PATH}")


if __name__ == "__main__":
    train()
