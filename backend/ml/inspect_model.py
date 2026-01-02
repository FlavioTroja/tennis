import pandas as pd
import joblib

MODEL_PATH = "/data/ml/tennis_model.joblib"

FEATURES = [
    "elo_diff",
    "ranking_diff",
    "recent_5_diff",
    "recent_10_diff",
    "surface_diff",
    "h2h_diff",
]


def inspect():
    pipeline = joblib.load(MODEL_PATH)

    model = pipeline.named_steps["model"]
    scaler = pipeline.named_steps["scaler"]

    coefs = model.coef_[0]

    df = pd.DataFrame({
        "feature": FEATURES,
        "coefficient": coefs,
        "abs_importance": abs(coefs)
    }).sort_values("abs_importance", ascending=False)

    print("\n📊 Importanza delle feature (Logistic Regression)\n")
    print(df.to_string(index=False))

    print("\n🧠 Interpretazione:")
    for _, r in df.iterrows():
        direction = "↑" if r.coefficient > 0 else "↓"
        print(f"- {r.feature}: {direction} aumenta probabilità vittoria Player A")


if __name__ == "__main__":
    inspect()
