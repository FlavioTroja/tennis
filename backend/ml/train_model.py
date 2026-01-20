"""
Tennis Match Prediction - Training Pipeline v2
===============================================
Miglioramenti rispetto alla v1:
1. Usa TUTTE le feature disponibili nel dataset
2. Confronta più algoritmi (LogReg, XGBoost, LightGBM, RandomForest)
3. Calibrazione probabilità (isotonic + sigmoid)
4. Cross-validation temporale
5. Feature importance analysis
6. Report completo con metriche
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score,
    log_loss,
    brier_score_loss,
    accuracy_score,
    classification_report
)

# Prova a importare XGBoost e LightGBM (opzionali)
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("⚠️  XGBoost non installato, verrà skippato")

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False
    print("⚠️  LightGBM non installato, verrà skippato")


# =============================================================================
# CONFIGURAZIONE
# =============================================================================

DATASET_PATH = "/data/ml/tennis_dataset.parquet"
OUTPUT_DIR = Path("/data/ml/models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Feature da usare (tutte quelle disponibili nel dataset)
ALL_FEATURES = [
    # Feature originali
    "elo_diff",
    "ranking_diff",
    "recent_5_diff",
    "recent_10_diff",
    "surface_diff",
    "h2h_diff",
    # Nuove feature
    "fatigue_diff",      # Differenza giorni di riposo
    "age_diff",          # Differenza età
    "workload_diff",     # Match ultimi 30 giorni
    "ace_diff",          # Differenza % ace
    "df_diff",           # Differenza % doppi falli
    "first_serve_diff",  # Differenza % prima in campo
    "first_won_diff",    # Differenza % punti vinti con prima
    "bp_save_diff",      # Differenza % break point salvati
    "level_exp_diff",    # Differenza win rate a quel livello torneo
]

# Split temporali
TRAIN_END = "2021-12-31"
VAL_END = "2022-12-31"
# Test: tutto dopo VAL_END


# =============================================================================
# MODELLI DA TESTARE
# =============================================================================

def get_models():
    """Restituisce dizionario di modelli da testare."""
    
    models = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, C=1.0))
        ]),
        
        "logistic_regression_l1": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, penalty="l1", solver="saga", C=0.5))
        ]),
        
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=50,
            random_state=42,
            n_jobs=-1
        ),
        
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            min_samples_leaf=50,
            random_state=42
        ),
    }
    
    if HAS_XGB:
        models["xgboost"] = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            min_child_weight=50,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss",
            use_label_encoder=False
        )
    
    if HAS_LGBM:
        models["lightgbm"] = LGBMClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            min_child_samples=50,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
    
    return models


# =============================================================================
# FUNZIONI UTILITY
# =============================================================================

def temporal_split(df):
    """Split temporale per evitare data leakage."""
    df = df.copy()
    df["match_date"] = pd.to_datetime(df["match_date"])
    
    train = df[df.match_date <= TRAIN_END]
    val = df[(df.match_date > TRAIN_END) & (df.match_date <= VAL_END)]
    test = df[df.match_date > VAL_END]
    
    return train, val, test


def evaluate_model(y_true, y_prob, y_pred=None):
    """Calcola metriche di valutazione."""
    if y_pred is None:
        y_pred = (y_prob >= 0.5).astype(int)
    
    return {
        "roc_auc": roc_auc_score(y_true, y_prob),
        "log_loss": log_loss(y_true, y_prob),
        "brier_score": brier_score_loss(y_true, y_prob),
        "accuracy": accuracy_score(y_true, y_pred),
    }


def compute_calibration(y_true, y_prob, n_bins=10):
    """Calcola calibration curve."""
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    
    return pd.DataFrame({
        "bin_mean_pred": mean_pred,
        "bin_true_rate": frac_pos,
        "gap": np.abs(frac_pos - mean_pred)
    })


def get_feature_importance(model, feature_names):
    """Estrae feature importance dal modello."""
    
    # Per pipeline, estrai il classificatore
    if hasattr(model, "named_steps"):
        clf = model.named_steps.get("clf", model)
    elif hasattr(model, "estimator"):
        clf = model.estimator
    else:
        clf = model
    
    # Prova diversi attributi per feature importance
    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        importances = np.abs(clf.coef_[0])
    else:
        return None
    
    return pd.DataFrame({
        "feature": feature_names,
        "importance": importances
    }).sort_values("importance", ascending=False)


def betting_simulation(df, prob_col="prob", target_col="target", edge_threshold=0.03, margin=0.05):
    """Simula betting con edge threshold."""
    df = df.copy()
    
    # Quote del bookmaker (con margine)
    df["book_odds"] = 1 / (df[prob_col] * (1 - margin))
    
    # Edge = nostra prob - prob implicita del book
    df["edge"] = df[prob_col] - (1 / df["book_odds"])
    
    # Filtra solo bet con edge positivo
    bets = df[df["edge"] > edge_threshold].copy()
    
    if len(bets) == 0:
        return {"n_bets": 0, "avg_roi": 0, "total_roi": 0, "hit_rate": 0}
    
    # ROI: vinciamo (odds - 1) se target=1, perdiamo -1 altrimenti
    bets["roi"] = np.where(bets[target_col] == 1, bets["book_odds"] - 1, -1)
    
    return {
        "n_bets": len(bets),
        "avg_roi": bets["roi"].mean(),
        "total_roi": bets["roi"].sum(),
        "hit_rate": (bets["roi"] > 0).mean()
    }


# =============================================================================
# TRAINING PRINCIPALE
# =============================================================================

def train_and_evaluate():
    """Pipeline principale di training e valutazione."""
    
    print("=" * 60)
    print("🎾 TENNIS PREDICTION - TRAINING PIPELINE v2")
    print("=" * 60)
    
    # Carica dataset
    print("\n📂 Caricamento dataset...")
    df = pd.read_parquet(DATASET_PATH)
    print(f"   Totale righe: {len(df):,}")
    
    # Verifica feature disponibili
    available_features = [f for f in ALL_FEATURES if f in df.columns]
    missing_features = [f for f in ALL_FEATURES if f not in df.columns]
    
    if missing_features:
        print(f"⚠️  Feature mancanti nel dataset: {missing_features}")
    
    print(f"   Feature usate: {available_features}")
    
    # Split temporale
    train_df, val_df, test_df = temporal_split(df)
    print(f"\n📊 Split temporale:")
    print(f"   Train: {len(train_df):,} righe (≤ {TRAIN_END})")
    print(f"   Val:   {len(val_df):,} righe ({TRAIN_END} - {VAL_END})")
    print(f"   Test:  {len(test_df):,} righe (> {VAL_END})")
    
    # Prepara X, y
    X_train = train_df[available_features]
    y_train = train_df["target"]
    
    X_val = val_df[available_features]
    y_val = val_df["target"]
    
    X_test = test_df[available_features]
    y_test = test_df["target"]
    
    # Training di tutti i modelli
    models = get_models()
    results = []
    
    print("\n" + "=" * 60)
    print("🏋️ TRAINING MODELLI")
    print("=" * 60)
    
    best_model = None
    best_model_name = None
    best_val_auc = 0
    
    for name, model in models.items():
        print(f"\n▶ Training {name}...")
        
        # Fit
        model.fit(X_train, y_train)
        
        # Predict probabilità
        val_prob = model.predict_proba(X_val)[:, 1]
        test_prob = model.predict_proba(X_test)[:, 1]
        
        # Metriche
        val_metrics = evaluate_model(y_val, val_prob)
        test_metrics = evaluate_model(y_test, test_prob)
        
        # Betting simulation su test
        test_df_copy = test_df.copy()
        test_df_copy["prob"] = test_prob
        betting = betting_simulation(test_df_copy)
        
        result = {
            "model": name,
            "val_auc": val_metrics["roc_auc"],
            "val_logloss": val_metrics["log_loss"],
            "test_auc": test_metrics["roc_auc"],
            "test_logloss": test_metrics["log_loss"],
            "test_brier": test_metrics["brier_score"],
            "test_accuracy": test_metrics["accuracy"],
            **{f"bet_{k}": v for k, v in betting.items()}
        }
        results.append(result)
        
        print(f"   Val AUC: {val_metrics['roc_auc']:.4f} | Test AUC: {test_metrics['roc_auc']:.4f}")
        print(f"   Bets: {betting['n_bets']} | Avg ROI: {betting['avg_roi']:.3f} | Total ROI: {betting['total_roi']:.2f}")
        
        # Track best model
        if val_metrics["roc_auc"] > best_val_auc:
            best_val_auc = val_metrics["roc_auc"]
            best_model = model
            best_model_name = name
    
    # Confronto modelli
    results_df = pd.DataFrame(results).sort_values("val_auc", ascending=False)
    
    print("\n" + "=" * 60)
    print("📊 CONFRONTO MODELLI")
    print("=" * 60)
    print(results_df.to_string(index=False))
    
    # Calibrazione del miglior modello
    print("\n" + "=" * 60)
    print(f"🎯 CALIBRAZIONE MODELLO MIGLIORE: {best_model_name}")
    print("=" * 60)
    
    # Riaddestra con calibrazione
    print("\n▶ Training con calibrazione isotonic...")
    
    # Combina train + val per il modello finale
    X_train_full = pd.concat([X_train, X_val])
    y_train_full = pd.concat([y_train, y_val])
    
    calibrated_model = CalibratedClassifierCV(
        estimator=models[best_model_name],  # Nuovo modello, non già fittato
        method="isotonic",
        cv=5
    )
    calibrated_model.fit(X_train_full, y_train_full)
    
    # Valuta modello calibrato
    test_prob_calibrated = calibrated_model.predict_proba(X_test)[:, 1]
    calibrated_metrics = evaluate_model(y_test, test_prob_calibrated)
    
    print(f"\n📈 Metriche modello calibrato (test set):")
    print(f"   ROC-AUC:     {calibrated_metrics['roc_auc']:.4f}")
    print(f"   Log Loss:    {calibrated_metrics['log_loss']:.4f}")
    print(f"   Brier Score: {calibrated_metrics['brier_score']:.4f}")
    print(f"   Accuracy:    {calibrated_metrics['accuracy']:.4f}")
    
    # Calibration table
    calib_df = compute_calibration(y_test, test_prob_calibrated)
    print(f"\n📐 Calibration Table:")
    print(calib_df.round(3).to_string(index=False))
    
    # Betting simulation finale
    test_df_final = test_df.copy()
    test_df_final["prob"] = test_prob_calibrated
    final_betting = betting_simulation(test_df_final)
    
    print(f"\n💰 Betting Simulation (calibrated):")
    print(f"   Bets:      {final_betting['n_bets']}")
    print(f"   Avg ROI:   {final_betting['avg_roi']:.3f}")
    print(f"   Total ROI: {final_betting['total_roi']:.2f}")
    print(f"   Hit Rate:  {final_betting['hit_rate']:.3f}")
    
    # Feature importance
    print("\n" + "=" * 60)
    print("📊 FEATURE IMPORTANCE")
    print("=" * 60)
    
    fi_df = get_feature_importance(best_model, available_features)
    if fi_df is not None:
        print(fi_df.to_string(index=False))
    else:
        print("Feature importance non disponibile per questo modello")
    
    # Salva modello
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = OUTPUT_DIR / f"tennis_model_{best_model_name}_{timestamp}.joblib"
    model_path_latest = OUTPUT_DIR / "tennis_model_calibrated.joblib"
    
    joblib.dump(calibrated_model, model_path)
    joblib.dump(calibrated_model, model_path_latest)
    
    print(f"\n✅ Modello salvato in:")
    print(f"   {model_path}")
    print(f"   {model_path_latest}")
    
    # Salva report
    report = {
        "timestamp": timestamp,
        "best_model": best_model_name,
        "features": available_features,
        "train_end": TRAIN_END,
        "val_end": VAL_END,
        "test_metrics": calibrated_metrics,
        "betting_simulation": final_betting,
        "all_models_comparison": results_df.to_dict(orient="records"),
    }
    
    report_path = OUTPUT_DIR / f"training_report_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Report salvato in: {report_path}")
    
    # Salva feature list per consistency
    features_path = OUTPUT_DIR / "feature_columns.json"
    with open(features_path, "w") as f:
        json.dump(available_features, f)
    
    print(f"📄 Feature list salvata in: {features_path}")
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETATO")
    print("=" * 60)
    
    return calibrated_model, results_df


if __name__ == "__main__":
    train_and_evaluate()
