"""
Tennis Match Prediction - Backtest v2
=====================================
Backtest completo con:
- Metriche ML (AUC, LogLoss, Brier)
- Calibration analysis
- Betting simulation con Kelly criterion
- Breakdown per superficie e tournament level
"""

import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from datetime import datetime

from sklearn.metrics import (
    roc_auc_score,
    log_loss,
    brier_score_loss,
    accuracy_score,
)
from sklearn.calibration import calibration_curve

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
MODEL_PATH = Path("/data/ml/models/tennis_model_calibrated.joblib")
FEATURES_PATH = Path("/data/ml/models/feature_columns.json")
OUTPUT_DIR = Path("/data/ml/backtest")

# Configurazione betting
EDGE_THRESHOLDS = [0.01, 0.02, 0.03, 0.05, 0.07, 0.10]
BOOK_MARGIN = 0.05  # Margine bookmaker simulato


def load_features():
    """Carica lista feature dal training."""
    if FEATURES_PATH.exists():
        with open(FEATURES_PATH) as f:
            return json.load(f)
    return ["elo_diff"]  # Fallback


def evaluate_predictions(y_true, y_prob):
    """Calcola metriche standard."""
    return {
        "roc_auc": roc_auc_score(y_true, y_prob),
        "log_loss": log_loss(y_true, y_prob),
        "brier_score": brier_score_loss(y_true, y_prob),
        "accuracy": accuracy_score(y_true, (y_prob >= 0.5).astype(int)),
    }


def calibration_analysis(y_true, y_prob, n_bins=10):
    """Analisi calibrazione."""
    frac_pos, mean_pred = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="uniform"
    )
    
    df = pd.DataFrame({
        "bin_center": mean_pred,
        "observed_rate": frac_pos,
        "gap": frac_pos - mean_pred,
        "abs_gap": np.abs(frac_pos - mean_pred),
    })
    
    # Expected Calibration Error (ECE)
    ece = df["abs_gap"].mean()
    
    return df, ece


def betting_simulation(df, edge_threshold=0.03, margin=BOOK_MARGIN):
    """
    Simula betting strategy.
    
    Assumiamo che le quote del book siano basate sulla nostra probabilità
    con un margine aggiunto (simulazione realistica).
    """
    df = df.copy()
    
    # Simula quote bookmaker (nostra prob + margine)
    df["book_odds"] = 1 / (df["prob"].clip(0.05, 0.95) * (1 + margin))
    
    # Implied probability dal book
    df["implied_prob"] = 1 / df["book_odds"]
    
    # Edge = nostra prob - implied prob
    df["edge"] = df["prob"] - df["implied_prob"]
    
    # Filtra bets con edge > threshold
    bets = df[df["edge"] > edge_threshold].copy()
    
    if len(bets) == 0:
        return {
            "threshold": edge_threshold,
            "n_bets": 0,
            "hit_rate": 0,
            "avg_odds": 0,
            "avg_edge": 0,
            "roi_flat": 0,
            "total_roi_flat": 0,
            "roi_kelly": 0,
            "total_roi_kelly": 0,
        }
    
    # Flat betting: 1 unità per bet
    bets["pnl_flat"] = np.where(
        bets["target"] == 1,
        bets["book_odds"] - 1,  # Win
        -1  # Loss
    )
    
    # Kelly betting: stake = edge / (odds - 1)
    bets["kelly_fraction"] = (bets["edge"] / (bets["book_odds"] - 1)).clip(0, 0.25)
    bets["pnl_kelly"] = np.where(
        bets["target"] == 1,
        bets["kelly_fraction"] * (bets["book_odds"] - 1),
        -bets["kelly_fraction"]
    )
    
    return {
        "threshold": edge_threshold,
        "n_bets": len(bets),
        "hit_rate": (bets["target"] == 1).mean(),
        "avg_odds": bets["book_odds"].mean(),
        "avg_edge": bets["edge"].mean(),
        "roi_flat": bets["pnl_flat"].mean(),
        "total_roi_flat": bets["pnl_flat"].sum(),
        "roi_kelly": bets["pnl_kelly"].mean(),
        "total_roi_kelly": bets["pnl_kelly"].sum(),
    }


def backtest():
    """Esegue backtest completo."""
    
    print("=" * 70)
    print("🎾 TENNIS PREDICTION - BACKTEST v2")
    print("=" * 70)
    
    # Carica modello e feature
    print("\n📂 Caricamento modello e dati...")
    
    if not MODEL_PATH.exists():
        print(f"❌ Modello non trovato: {MODEL_PATH}")
        print("   Esegui prima train_model_v2.py")
        return
    
    model = joblib.load(MODEL_PATH)
    features = load_features()
    
    print(f"   Modello: {MODEL_PATH}")
    print(f"   Feature: {features}")
    
    # Carica dataset
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])
    
    # Test set: dati 2023+
    test_df = df[df.match_date > "2022-12-31"].copy()
    
    print(f"   Test set: {len(test_df):,} righe")
    
    # Verifica feature disponibili
    missing = [f for f in features if f not in test_df.columns]
    if missing:
        print(f"⚠️  Feature mancanti: {missing}")
        features = [f for f in features if f in test_df.columns]
    
    # Predizioni
    X_test = test_df[features]
    y_test = test_df["target"]
    
    probs = model.predict_proba(X_test)[:, 1]
    test_df["prob"] = probs
    
    # =================================================================
    # METRICHE ML
    # =================================================================
    print("\n" + "=" * 70)
    print("📊 METRICHE ML")
    print("=" * 70)
    
    metrics = evaluate_predictions(y_test, probs)
    
    print(f"\n   ROC-AUC:     {metrics['roc_auc']:.4f}")
    print(f"   Log Loss:    {metrics['log_loss']:.4f}")
    print(f"   Brier Score: {metrics['brier_score']:.4f}")
    print(f"   Accuracy:    {metrics['accuracy']:.4f}")
    
    # =================================================================
    # CALIBRATION
    # =================================================================
    print("\n" + "=" * 70)
    print("📐 CALIBRATION ANALYSIS")
    print("=" * 70)
    
    calib_df, ece = calibration_analysis(y_test, probs)
    
    print(f"\n   Expected Calibration Error (ECE): {ece:.4f}")
    print("\n   Calibration Table:")
    print(calib_df.round(3).to_string(index=False))
    
    # =================================================================
    # BETTING SIMULATION
    # =================================================================
    print("\n" + "=" * 70)
    print("💰 BETTING SIMULATION")
    print("=" * 70)
    
    betting_results = []
    
    for threshold in EDGE_THRESHOLDS:
        result = betting_simulation(test_df, edge_threshold=threshold)
        betting_results.append(result)
    
    betting_df = pd.DataFrame(betting_results)
    
    print(f"\n   Book Margin: {BOOK_MARGIN:.0%}")
    print("\n   Results by Edge Threshold:")
    print(betting_df.round(3).to_string(index=False))
    
    # =================================================================
    # BREAKDOWN PER PROBABILITÀ
    # =================================================================
    print("\n" + "=" * 70)
    print("📊 BREAKDOWN PER CONFIDENCE")
    print("=" * 70)
    
    test_df["prob_bin"] = pd.cut(
        test_df["prob"],
        bins=[0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0],
        labels=["<30%", "30-40%", "40-50%", "50-60%", "60-70%", ">70%"]
    )
    
    conf_breakdown = test_df.groupby("prob_bin", observed=True).agg({
        "target": ["count", "mean"],
        "prob": "mean"
    }).round(3)
    
    conf_breakdown.columns = ["n_matches", "actual_win_rate", "predicted_prob"]
    print(conf_breakdown)
    
    # =================================================================
    # SALVA REPORT
    # =================================================================
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "timestamp": timestamp,
        "model_path": str(MODEL_PATH),
        "features": features,
        "test_set_size": len(test_df),
        "metrics": metrics,
        "ece": ece,
        "betting_simulation": betting_results,
    }
    
    report_path = OUTPUT_DIR / f"backtest_report_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    # Salva anche predizioni per analisi
    preds_path = OUTPUT_DIR / f"predictions_{timestamp}.parquet"
    test_df[["match_date", "prob", "target"]].to_parquet(preds_path)
    
    print(f"\n✅ Report salvato: {report_path}")
    print(f"✅ Predizioni salvate: {preds_path}")
    
    print("\n" + "=" * 70)
    print("✅ BACKTEST COMPLETATO")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    backtest()
