"""
Tennis Match Prediction - Ablation Study
=========================================
Confronta diverse combinazioni di feature per capire
quali contribuiscono maggiormente alle predizioni.
"""

import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss

DATASET_PATH = "/data/ml/tennis_dataset.parquet"

EDGE_THRESHOLD = 0.03
BOOK_MARGIN = 0.05

# Configurazioni feature da testare
CONFIGS = {
    "full": [
        "elo_diff",
        "ranking_diff",
        "recent_5_diff",
        "recent_10_diff",
        "surface_diff",
        "h2h_diff",
    ],
    "no_ranking": [
        "elo_diff",
        "recent_5_diff",
        "recent_10_diff",
        "surface_diff",
        "h2h_diff",
    ],
    "no_h2h": [
        "elo_diff",
        "ranking_diff",
        "recent_5_diff",
        "recent_10_diff",
        "surface_diff",
    ],
    "elo_form": [
        "elo_diff",
        "recent_5_diff",
        "recent_10_diff",
    ],
    "elo_surface": [
        "elo_diff",
        "surface_diff",
    ],
    "elo_only": [
        "elo_diff",
    ],
    "no_elo": [
        "ranking_diff",
        "recent_5_diff",
        "recent_10_diff",
        "surface_diff",
        "h2h_diff",
    ],
}


def temporal_split(df):
    """Split temporale: train ≤2021, test >2022."""
    train = df[df.match_date <= "2021-12-31"]
    test = df[df.match_date > "2022-12-31"]
    return train, test


def run_experiment(df, features):
    """Esegue training e valutazione per un set di feature."""
    
    train_df, test_df = temporal_split(df)
    
    X_train = train_df[features]
    y_train = train_df["target"]
    
    X_test = test_df[features]
    y_test = test_df["target"]
    
    # Modello
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000))
    ])
    
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    
    # Metriche ML
    roc = roc_auc_score(y_test, probs)
    ll = log_loss(y_test, probs)
    brier = brier_score_loss(y_test, probs)
    
    # Betting simulation
    test_df = test_df.copy()
    test_df["prob"] = probs
    test_df["book_odds"] = 1 / (test_df["prob"] * (1 - BOOK_MARGIN))
    test_df["edge"] = test_df["prob"] - (1 / test_df["book_odds"])
    
    bets = test_df[test_df["edge"] > EDGE_THRESHOLD].copy()
    
    if len(bets) == 0:
        return roc, ll, brier, 0, 0.0, 0.0
    
    bets["roi"] = np.where(bets["target"] == 1, bets["book_odds"] - 1, -1)
    
    return (
        roc,
        ll,
        brier,
        len(bets),
        bets["roi"].mean(),
        bets["roi"].sum()
    )


def main():
    """Esegue ablation study su tutte le configurazioni."""
    
    print("=" * 70)
    print("🔬 ABLATION STUDY - Feature Importance Analysis")
    print("=" * 70)
    
    # Carica dataset
    df = pd.read_parquet(DATASET_PATH)
    df["match_date"] = pd.to_datetime(df["match_date"])
    
    print(f"\n📂 Dataset: {len(df):,} righe")
    
    results = []
    
    for name, features in CONFIGS.items():
        # Verifica che tutte le feature esistano
        missing = [f for f in features if f not in df.columns]
        if missing:
            print(f"⚠️  Skip {name}: feature mancanti {missing}")
            continue
        
        roc, ll, brier, n_bets, avg_roi, tot_roi = run_experiment(df, features)
        
        results.append({
            "config": name,
            "n_features": len(features),
            "features": ", ".join(features),
            "roc_auc": round(roc, 4),
            "logloss": round(ll, 4),
            "brier": round(brier, 4),
            "n_bets": n_bets,
            "avg_roi": round(avg_roi, 4),
            "total_roi": round(tot_roi, 2),
        })
    
    # Risultati
    res_df = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
    
    print("\n" + "=" * 70)
    print("📊 RISULTATI")
    print("=" * 70)
    
    # Tabella compatta
    compact_df = res_df[["config", "n_features", "roc_auc", "logloss", "n_bets", "avg_roi", "total_roi"]]
    print(compact_df.to_string(index=False))
    
    # Best config
    best = res_df.iloc[0]
    print(f"\n🏆 Migliore configurazione: {best['config']}")
    print(f"   ROC-AUC: {best['roc_auc']:.4f}")
    print(f"   Feature: {best['features']}")
    
    # Feature importance (quanto peggiora rimuovendo ogni feature)
    print("\n" + "=" * 70)
    print("📈 FEATURE IMPORTANCE (drop in AUC when removed)")
    print("=" * 70)
    
    full_auc = res_df[res_df["config"] == "full"]["roc_auc"].values[0]
    
    importance = []
    for name, row in res_df.iterrows():
        if row["config"] != "full" and row["config"].startswith("no_"):
            removed = row["config"].replace("no_", "")
            drop = full_auc - row["roc_auc"]
            importance.append({"feature_removed": removed, "auc_drop": drop})
    
    if importance:
        imp_df = pd.DataFrame(importance).sort_values("auc_drop", ascending=False)
        print(imp_df.to_string(index=False))


if __name__ == "__main__":
    main()
