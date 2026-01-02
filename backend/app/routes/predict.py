from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib

from app.services.feature_service import (
    get_player_id,
    get_surface_state,
)

MODEL_PATH = "/data/ml/tennis_model.joblib"

router = APIRouter()
model = joblib.load(MODEL_PATH)


class PredictRequest(BaseModel):
    player_a: str
    player_b: str
    surface: str


@router.post("/predict")
def predict(req: PredictRequest):
    try:
        A = get_player_id(req.player_a)
        B = get_player_id(req.player_b)
        surface = req.surface

        elo_A, _ = get_surface_state(A, surface)
        elo_B, _ = get_surface_state(B, surface)

        elo_diff = elo_A - elo_B

        # ⚠️ DataFrame con feature name (niente warning sklearn)
        X = pd.DataFrame(
            [{"elo_diff": elo_diff}]
        )

        prob = model.predict_proba(X)[0]

        return {
            "player_a": req.player_a,
            "player_b": req.player_b,
            "surface": surface,
            "player_a_win_probability": round(float(prob[1]), 3),
            "player_b_win_probability": round(float(prob[0]), 3),
            "elo_diff": round(elo_diff, 2),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
