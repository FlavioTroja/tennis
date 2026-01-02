from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib

from ml.feature_pipeline import (
    compute_features_row,
    FEATURE_COLUMNS,
)

MODEL_PATH = "/data/ml/tennis_model_calibrated.joblib"

router = APIRouter()
model = joblib.load(MODEL_PATH)


class PredictRequest(BaseModel):
    player_a: str
    player_b: str
    surface: str


@router.post("/predict")
def predict(req: PredictRequest):
    try:
        features = compute_features_row(
            req.player_a,
            req.player_b,
            req.surface,
        )

        X = pd.DataFrame([features], columns=FEATURE_COLUMNS)

        prob = model.predict_proba(X)[0]

        return {
            "player_a": req.player_a,
            "player_b": req.player_b,
            "surface": req.surface,
            "player_a_win_probability": round(float(prob[1]), 3),
            "player_b_win_probability": round(float(prob[0]), 3),
            "features": {k: round(v, 3) for k, v in features.items()},
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
