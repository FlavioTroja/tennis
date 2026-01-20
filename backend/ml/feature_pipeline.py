"""
Tennis Match Prediction - Feature Pipeline
===========================================
Pipeline per calcolare le feature in tempo reale per predizioni live.
Allineato con train_model.py per usare TUTTE le feature.
"""

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from app.services.feature_service import (
    get_player_id,
    get_surface_state,
    get_form,
    get_h2h,
    get_latest_rank,
    get_days_since_last_match,
    get_player_age,
    get_matches_last_30_days,
    get_serve_stats,
    get_level_experience,
)

# Carica la lista delle feature dal training (per consistency)
FEATURES_PATH = Path("/data/ml/models/feature_columns.json")

# Default feature se il file non esiste
DEFAULT_FEATURES = [
    # Feature originali
    "elo_diff",
    "ranking_diff",
    "recent_5_diff",
    "recent_10_diff",
    "surface_diff",
    "h2h_diff",
    # Nuove feature
    "fatigue_diff",
    "age_diff",
    "workload_diff",
    "ace_diff",
    "df_diff",
    "first_serve_diff",
    "first_won_diff",
    "bp_save_diff",
    "level_exp_diff",
]


def load_feature_columns():
    """Carica le feature usate nel training."""
    if FEATURES_PATH.exists():
        with open(FEATURES_PATH) as f:
            return json.load(f)
    return DEFAULT_FEATURES


FEATURE_COLUMNS = load_feature_columns()


def compute_player_features(player_name: str, opponent_name: str, surface: str, level: str = "A") -> Dict:
    """
    Calcola tutte le feature per UN giocatore rispetto all'avversario.
    
    Returns:
        Dict con tutte le feature raw del giocatore
    """
    player_id = get_player_id(player_name)
    opponent_id = get_player_id(opponent_name)
    
    # Elo e win rate su superficie
    elo, surface_wr = get_surface_state(player_id, surface)
    
    # Form recente
    recent_5, recent_10 = get_form(player_id)
    
    # Head to head
    h2h_wins = get_h2h(player_id, opponent_id)
    
    # Ranking
    rank = get_latest_rank(player_id)
    
    # Nuove feature
    days_rest = get_days_since_last_match(player_id)
    age = get_player_age(player_id)
    matches_30d = get_matches_last_30_days(player_id)
    serve_stats = get_serve_stats(player_id)
    level_wr = get_level_experience(player_id, level)
    
    return {
        "elo": elo,
        "surface_wr": surface_wr,
        "recent_5": recent_5,
        "recent_10": recent_10,
        "h2h_wins": h2h_wins,
        "rank": rank,
        "days_rest": days_rest,
        "age": age,
        "matches_30d": matches_30d,
        "ace_pct": serve_stats["ace_pct"],
        "df_pct": serve_stats["df_pct"],
        "first_serve_pct": serve_stats["first_serve_pct"],
        "first_won_pct": serve_stats["first_won_pct"],
        "bp_save_pct": serve_stats["bp_save_pct"],
        "level_wr": level_wr,
    }


def compute_features_row(
    player_a: str,
    player_b: str,
    surface: str,
    level: str = "A",
) -> Dict:
    """
    Calcola le feature DIFFERENZIALI per una partita.
    Usata da API /predict e odds pipeline.
    
    Returns:
        Dict con tutte le feature *_diff
    """
    
    # Feature giocatore A
    feat_a = compute_player_features(player_a, player_b, surface, level)
    
    # Feature giocatore B
    feat_b = compute_player_features(player_b, player_a, surface, level)
    
    # Calcola differenze (A - B)
    features = {
        # Feature originali
        "elo_diff": feat_a["elo"] - feat_b["elo"],
        "ranking_diff": feat_a["rank"] - feat_b["rank"],
        "recent_5_diff": feat_a["recent_5"] - feat_b["recent_5"],
        "recent_10_diff": feat_a["recent_10"] - feat_b["recent_10"],
        "surface_diff": feat_a["surface_wr"] - feat_b["surface_wr"],
        "h2h_diff": feat_a["h2h_wins"] - feat_b["h2h_wins"],
        # Nuove feature
        "fatigue_diff": feat_b["days_rest"] - feat_a["days_rest"],  # Positivo = B più riposato
        "age_diff": feat_a["age"] - feat_b["age"],
        "workload_diff": feat_a["matches_30d"] - feat_b["matches_30d"],
        "ace_diff": feat_a["ace_pct"] - feat_b["ace_pct"],
        "df_diff": feat_a["df_pct"] - feat_b["df_pct"],
        "first_serve_diff": feat_a["first_serve_pct"] - feat_b["first_serve_pct"],
        "first_won_diff": feat_a["first_won_pct"] - feat_b["first_won_pct"],
        "bp_save_diff": feat_a["bp_save_pct"] - feat_b["bp_save_pct"],
        "level_exp_diff": feat_a["level_wr"] - feat_b["level_wr"],
    }
    
    # Filtra solo le feature usate dal modello
    return {k: v for k, v in features.items() if k in FEATURE_COLUMNS}


def compute_features_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola le feature per un DataFrame di match.
    Usata da odds pipeline e backtest.
    
    Input DataFrame deve avere colonne: player_a, player_b, surface
    """
    
    rows = []
    
    for _, r in df.iterrows():
        try:
            level = getattr(r, 'tournament_level', 'A') or 'A'
            features = compute_features_row(
                player_a=r.player_a,
                player_b=r.player_b,
                surface=r.surface,
                level=level,
            )
            rows.append({**r.to_dict(), **features})
        except ValueError as e:
            print(f"⚠️ Skip match {r.player_a} vs {r.player_b}: {e}")
            continue
    
    return pd.DataFrame(rows)


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Restituisce SOLO le colonne feature.
    Ordine garantito per sklearn.
    """
    return df[FEATURE_COLUMNS]


def get_features_with_details(
    player_a: str,
    player_b: str,
    surface: str,
    level: str = "A",
) -> Tuple[Dict, Dict, Dict]:
    """
    Versione estesa che restituisce anche i dettagli per giocatore.
    Utile per l'API per mostrare breakdown delle feature.
    
    Returns:
        Tuple di (features_diff, features_a, features_b)
    """
    
    feat_a = compute_player_features(player_a, player_b, surface, level)
    feat_b = compute_player_features(player_b, player_a, surface, level)
    
    features_diff = {
        # Feature originali
        "elo_diff": feat_a["elo"] - feat_b["elo"],
        "ranking_diff": feat_a["rank"] - feat_b["rank"],
        "recent_5_diff": feat_a["recent_5"] - feat_b["recent_5"],
        "recent_10_diff": feat_a["recent_10"] - feat_b["recent_10"],
        "surface_diff": feat_a["surface_wr"] - feat_b["surface_wr"],
        "h2h_diff": feat_a["h2h_wins"] - feat_b["h2h_wins"],
        # Nuove feature
        "fatigue_diff": feat_b["days_rest"] - feat_a["days_rest"],
        "age_diff": feat_a["age"] - feat_b["age"],
        "workload_diff": feat_a["matches_30d"] - feat_b["matches_30d"],
        "ace_diff": feat_a["ace_pct"] - feat_b["ace_pct"],
        "df_diff": feat_a["df_pct"] - feat_b["df_pct"],
        "first_serve_diff": feat_a["first_serve_pct"] - feat_b["first_serve_pct"],
        "first_won_diff": feat_a["first_won_pct"] - feat_b["first_won_pct"],
        "bp_save_diff": feat_a["bp_save_pct"] - feat_b["bp_save_pct"],
        "level_exp_diff": feat_a["level_wr"] - feat_b["level_wr"],
    }
    
    return features_diff, feat_a, feat_b


# Mantieni compatibilità
__all__ = [
    "FEATURE_COLUMNS",
    "compute_features_row",
    "compute_features_df",
    "get_feature_matrix",
    "get_features_with_details",
]
