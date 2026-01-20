"""
Tennis Match Prediction - API Routes
====================================
Endpoint per predizioni match.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import pandas as pd
import joblib
from pathlib import Path

from ml.feature_pipeline import (
    compute_features_row,
    get_features_with_details,
    FEATURE_COLUMNS,
)

MODEL_PATH = Path("/data/ml/models/tennis_model_calibrated.joblib")

router = APIRouter(tags=["predictions"])

# Carica modello all'avvio
try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
except Exception as e:
    print(f"⚠️ Modello non caricato: {e}")
    MODEL_LOADED = False
    model = None


class PredictRequest(BaseModel):
    player_a: str
    player_b: str
    surface: str
    odds_a: Optional[float] = None
    odds_b: Optional[float] = None


class PredictResponse(BaseModel):
    player_a: str
    player_b: str
    surface: str
    prob_a: float
    prob_b: float
    features: Dict[str, float]
    player_a_details: Dict[str, float]
    player_b_details: Dict[str, float]
    edge_a: Optional[float] = None
    edge_b: Optional[float] = None
    value_bet: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    features: list


@router.get("/model/health", response_model=HealthResponse)
def model_health():
    """Verifica stato del modello."""
    return {
        "status": "ok" if MODEL_LOADED else "degraded",
        "model_loaded": MODEL_LOADED,
        "features": FEATURE_COLUMNS,
    }


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """
    Predice la probabilità di vittoria per una partita.
    
    Se vengono fornite le quote (odds_a, odds_b), calcola anche l'edge
    e suggerisce se c'è una value bet.
    """
    
    if not MODEL_LOADED:
        raise HTTPException(
            status_code=503,
            detail="Modello non disponibile. Esegui prima il training."
        )
    
    try:
        # Calcola feature con dettagli
        features_diff, feat_a, feat_b = get_features_with_details(
            req.player_a,
            req.player_b,
            req.surface,
        )
        
        # Filtra solo feature usate dal modello
        model_features = {k: v for k, v in features_diff.items() if k in FEATURE_COLUMNS}
        
        # Prepara input per modello
        X = pd.DataFrame([model_features], columns=FEATURE_COLUMNS)
        
        # Predizione
        prob = model.predict_proba(X)[0]
        prob_a = float(prob[1])
        prob_b = float(prob[0])
        
        # Calcola edge se quote fornite
        edge_a = None
        edge_b = None
        value_bet = None
        
        EDGE_THRESHOLD = 0.03
        
        if req.odds_a and req.odds_b:
            implied_a = 1 / req.odds_a
            implied_b = 1 / req.odds_b
            
            edge_a = prob_a - implied_a
            edge_b = prob_b - implied_b
            
            if edge_a >= EDGE_THRESHOLD:
                value_bet = f"BET {req.player_a} (edge: {edge_a:.1%})"
            elif edge_b >= EDGE_THRESHOLD:
                value_bet = f"BET {req.player_b} (edge: {edge_b:.1%})"
            else:
                value_bet = "NO VALUE"
        
        return PredictResponse(
            player_a=req.player_a,
            player_b=req.player_b,
            surface=req.surface,
            prob_a=round(prob_a, 4),
            prob_b=round(prob_b, 4),
            features={k: round(v, 3) for k, v in model_features.items()},
            player_a_details={k: round(v, 3) for k, v in feat_a.items()},
            player_b_details={k: round(v, 3) for k, v in feat_b.items()},
            edge_a=round(edge_a, 4) if edge_a else None,
            edge_b=round(edge_b, 4) if edge_b else None,
            value_bet=value_bet,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore predizione: {str(e)}")


@router.post("/predict/batch")
def predict_batch(matches: list[PredictRequest]):
    """Predizione batch per più partite."""
    
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Modello non disponibile")
    
    results = []
    
    for match in matches:
        try:
            result = predict(match)
            results.append(result.model_dump())
        except HTTPException as e:
            results.append({
                "player_a": match.player_a,
                "player_b": match.player_b,
                "error": e.detail
            })
    
    return results


@router.get("/model/info")
def model_info():
    """Informazioni sul modello caricato."""
    
    if not MODEL_LOADED:
        return {"error": "Modello non caricato"}
    
    info = {
        "model_path": str(MODEL_PATH),
        "features": FEATURE_COLUMNS,
        "model_type": type(model).__name__,
    }
    
    if hasattr(model, "estimator"):
        info["base_estimator"] = type(model.estimator).__name__
    
    return info
