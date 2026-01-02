import pandas as pd
import joblib

MODEL_PATH = "/data/ml/tennis_model.joblib"
FEATURES = ["elo_diff"]

_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_proba_from_features(features: dict) -> float:
    """
    Ritorna P(player A wins)
    """
    X = pd.DataFrame([features], columns=FEATURES)
    model = get_model()
    return float(model.predict_proba(X)[0, 1])
