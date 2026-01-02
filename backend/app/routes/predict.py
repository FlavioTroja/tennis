from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import joblib

from app.services.feature_service import (
    get_player_id,
    get_surface_state,
    get_form,
    get_h2h,
    get_latest_rank,
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

        elo_A, surf_A = get_surface_state(A, surface)
        elo_B, surf_B = get_surface_state(B, surface)

        r5_A, r10_A = get_form(A)
        r5_B, r10_B = get_form(B)

        h2h_A = get_h2h(A, B)
        h2h_B = get_h2h(B, A)

        rank_A = get_latest_rank(A)
        rank_B = get_latest_rank(B)

        features = {
            "elo_diff": elo_A - elo_B,
            "ranking_diff": rank_A - rank_B,
            "recent_5_diff": r5_A - r5_B,
            "recent_10_diff": r10_A - r10_B,
            "surface_diff": surf_A - surf_B,
            "h2h_diff": h2h_A - h2h_B,
        }

        X = [[
            features["elo_diff"],
            features["ranking_diff"],
            features["recent_5_diff"],
            features["recent_10_diff"],
            features["surface_diff"],
            features["h2h_diff"],
        ]]

        prob = model.predict_proba(X)[0]

        return {
            "player_a": req.player_a,
            "player_b": req.player_b,
            "surface": surface,
            "player_a_win_probability": round(float(prob[1]), 3),
            "player_b_win_probability": round(float(prob[0]), 3),
            "features": {k: round(v, 3) for k, v in features.items()}
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
