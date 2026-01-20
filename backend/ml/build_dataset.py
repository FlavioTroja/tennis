"""
Tennis Match Prediction - Dataset Builder
==========================================
Costruisce il dataset ML dal feature store (player_match_features).
Usa le feature PRE-MATCH calcolate da feature_store_build.py.
"""

import pandas as pd
from sqlalchemy import text
from tqdm import tqdm

from app.database import engine

OUTPUT_PATH = "/data/ml/tennis_dataset.parquet"


def build_dataset():
    """
    Costruisce il dataset per il training ML.
    
    Legge da player_match_features (popolato da feature_store_build.py)
    e crea righe con feature differenziali (A - B) per ogni match.
    """
    
    print("📂 Caricamento match dal feature store...")
    
    # Query per ottenere tutte le feature pre-match
    # Ogni match ha 2 righe in player_match_features (una per giocatore)
    query = """
    SELECT 
        m.id as match_id,
        m.match_date,
        m.surface,
        m.tournament_level,
        m.winner_id,
        m.loser_id,
        -- Feature winner (pre-match)
        fw.elo as winner_elo,
        fw.recent_5 as winner_recent_5,
        fw.recent_10 as winner_recent_10,
        fw.surface_wr as winner_surface_wr,
        fw.h2h_wins as winner_h2h,
        fw.rank as winner_rank,
        fw.days_since_last_match as winner_days_rest,
        fw.age as winner_age,
        fw.matches_last_30d as winner_matches_30d,
        fw.ace_pct as winner_ace_pct,
        fw.df_pct as winner_df_pct,
        fw.first_serve_pct as winner_first_serve_pct,
        fw.first_serve_won_pct as winner_first_won_pct,
        fw.bp_save_pct as winner_bp_save_pct,
        fw.level_win_rate as winner_level_wr,
        -- Feature loser (pre-match)
        fl.elo as loser_elo,
        fl.recent_5 as loser_recent_5,
        fl.recent_10 as loser_recent_10,
        fl.surface_wr as loser_surface_wr,
        fl.h2h_wins as loser_h2h,
        fl.rank as loser_rank,
        fl.days_since_last_match as loser_days_rest,
        fl.age as loser_age,
        fl.matches_last_30d as loser_matches_30d,
        fl.ace_pct as loser_ace_pct,
        fl.df_pct as loser_df_pct,
        fl.first_serve_pct as loser_first_serve_pct,
        fl.first_serve_won_pct as loser_first_won_pct,
        fl.bp_save_pct as loser_bp_save_pct,
        fl.level_win_rate as loser_level_wr
    FROM matches m
    JOIN player_match_features fw 
        ON fw.match_id = m.id AND fw.player_id = m.winner_id
    JOIN player_match_features fl 
        ON fl.match_id = m.id AND fl.player_id = m.loser_id
    WHERE m.surface IN ('Hard', 'Clay', 'Grass')
    ORDER BY m.match_date ASC, m.id ASC
    """
    
    df = pd.read_sql(query, engine)
    
    print(f"   Match trovati: {len(df):,}")
    
    if len(df) == 0:
        print("❌ Nessun match trovato. Esegui prima:")
        print("   1. python -m importer.import_csv")
        print("   2. python -m ml.feature_store_build")
        return
    
    print("🔧 Costruzione feature differenziali...")
    
    rows = []
    
    for _, m in tqdm(df.iterrows(), total=len(df), desc="Building dataset"):
        # Feature base
        winner_elo = m.winner_elo if pd.notna(m.winner_elo) else 1500.0
        loser_elo = m.loser_elo if pd.notna(m.loser_elo) else 1500.0
        
        winner_r5 = m.winner_recent_5 if pd.notna(m.winner_recent_5) else 0.0
        loser_r5 = m.loser_recent_5 if pd.notna(m.loser_recent_5) else 0.0
        
        winner_r10 = m.winner_recent_10 if pd.notna(m.winner_recent_10) else 0.0
        loser_r10 = m.loser_recent_10 if pd.notna(m.loser_recent_10) else 0.0
        
        winner_surf = m.winner_surface_wr if pd.notna(m.winner_surface_wr) else 0.0
        loser_surf = m.loser_surface_wr if pd.notna(m.loser_surface_wr) else 0.0
        
        winner_h2h = int(m.winner_h2h) if pd.notna(m.winner_h2h) else 0
        loser_h2h = int(m.loser_h2h) if pd.notna(m.loser_h2h) else 0
        
        winner_rank = int(m.winner_rank) if pd.notna(m.winner_rank) else 500
        loser_rank = int(m.loser_rank) if pd.notna(m.loser_rank) else 500
        
        # Nuove feature
        winner_days_rest = int(m.winner_days_rest) if pd.notna(m.winner_days_rest) else 7
        loser_days_rest = int(m.loser_days_rest) if pd.notna(m.loser_days_rest) else 7
        
        winner_age = float(m.winner_age) if pd.notna(m.winner_age) else 25.0
        loser_age = float(m.loser_age) if pd.notna(m.loser_age) else 25.0
        
        winner_m30d = int(m.winner_matches_30d) if pd.notna(m.winner_matches_30d) else 0
        loser_m30d = int(m.loser_matches_30d) if pd.notna(m.loser_matches_30d) else 0
        
        winner_ace = float(m.winner_ace_pct) if pd.notna(m.winner_ace_pct) else 0.0
        loser_ace = float(m.loser_ace_pct) if pd.notna(m.loser_ace_pct) else 0.0
        
        winner_df = float(m.winner_df_pct) if pd.notna(m.winner_df_pct) else 0.0
        loser_df = float(m.loser_df_pct) if pd.notna(m.loser_df_pct) else 0.0
        
        winner_1st_pct = float(m.winner_first_serve_pct) if pd.notna(m.winner_first_serve_pct) else 0.0
        loser_1st_pct = float(m.loser_first_serve_pct) if pd.notna(m.loser_first_serve_pct) else 0.0
        
        winner_1st_won = float(m.winner_first_won_pct) if pd.notna(m.winner_first_won_pct) else 0.0
        loser_1st_won = float(m.loser_first_won_pct) if pd.notna(m.loser_first_won_pct) else 0.0
        
        winner_bp_save = float(m.winner_bp_save_pct) if pd.notna(m.winner_bp_save_pct) else 0.0
        loser_bp_save = float(m.loser_bp_save_pct) if pd.notna(m.loser_bp_save_pct) else 0.0
        
        winner_level_wr = float(m.winner_level_wr) if pd.notna(m.winner_level_wr) else 0.0
        loser_level_wr = float(m.loser_level_wr) if pd.notna(m.loser_level_wr) else 0.0
        
        # Riga 1: Winner come player A (target = 1)
        rows.append({
            "match_id": m.match_id,
            "match_date": m.match_date,
            "surface": m.surface,
            # Feature originali
            "elo_diff": round(winner_elo - loser_elo, 2),
            "ranking_diff": winner_rank - loser_rank,
            "recent_5_diff": round(winner_r5 - loser_r5, 4),
            "recent_10_diff": round(winner_r10 - loser_r10, 4),
            "surface_diff": round(winner_surf - loser_surf, 4),
            "h2h_diff": winner_h2h - loser_h2h,
            # Nuove feature
            "fatigue_diff": loser_days_rest - winner_days_rest,  # Positivo = avversario più riposato
            "age_diff": winner_age - loser_age,
            "workload_diff": winner_m30d - loser_m30d,  # Match giocati ultimi 30gg
            "ace_diff": round(winner_ace - loser_ace, 4),
            "df_diff": round(winner_df - loser_df, 4),  # Negativo è meglio
            "first_serve_diff": round(winner_1st_pct - loser_1st_pct, 4),
            "first_won_diff": round(winner_1st_won - loser_1st_won, 4),
            "bp_save_diff": round(winner_bp_save - loser_bp_save, 4),
            "level_exp_diff": round(winner_level_wr - loser_level_wr, 4),
            "target": 1,
        })
        
        # Riga 2: Loser come player A (target = 0, simmetrica)
        rows.append({
            "match_id": m.match_id,
            "match_date": m.match_date,
            "surface": m.surface,
            # Feature originali (invertite)
            "elo_diff": round(loser_elo - winner_elo, 2),
            "ranking_diff": loser_rank - winner_rank,
            "recent_5_diff": round(loser_r5 - winner_r5, 4),
            "recent_10_diff": round(loser_r10 - winner_r10, 4),
            "surface_diff": round(loser_surf - winner_surf, 4),
            "h2h_diff": loser_h2h - winner_h2h,
            # Nuove feature (invertite)
            "fatigue_diff": winner_days_rest - loser_days_rest,
            "age_diff": loser_age - winner_age,
            "workload_diff": loser_m30d - winner_m30d,
            "ace_diff": round(loser_ace - winner_ace, 4),
            "df_diff": round(loser_df - winner_df, 4),
            "first_serve_diff": round(loser_1st_pct - winner_1st_pct, 4),
            "first_won_diff": round(loser_1st_won - winner_1st_won, 4),
            "bp_save_diff": round(loser_bp_save - winner_bp_save, 4),
            "level_exp_diff": round(loser_level_wr - winner_level_wr, 4),
            "target": 0,
        })
    
    # Crea DataFrame
    dataset = pd.DataFrame(rows)
    
    # Salva
    dataset.to_parquet(OUTPUT_PATH, index=False)
    
    print(f"\n✅ Dataset salvato: {OUTPUT_PATH}")
    print(f"   Righe totali: {len(dataset):,}")
    print(f"   Match unici: {dataset['match_id'].nunique():,}")
    print(f"\n📊 Statistiche feature:")
    print(dataset.describe().round(2))
    print(f"\n📅 Range date: {dataset['match_date'].min()} → {dataset['match_date'].max()}")


def verify_dataset():
    """Verifica che il dataset sia valido."""
    
    print("\n🔍 Verifica dataset...")
    
    try:
        df = pd.read_parquet(OUTPUT_PATH)
    except FileNotFoundError:
        print(f"❌ Dataset non trovato: {OUTPUT_PATH}")
        return False
    
    required_cols = [
        "elo_diff", "ranking_diff", "recent_5_diff", 
        "recent_10_diff", "surface_diff", "h2h_diff", 
        "target", "match_date"
    ]
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ Colonne mancanti: {missing}")
        return False
    
    # Check NaN
    nan_counts = df[required_cols].isna().sum()
    if nan_counts.sum() > 0:
        print(f"⚠️  Valori NaN trovati:")
        print(nan_counts[nan_counts > 0])
    
    # Check target
    if not set(df["target"].unique()).issubset({0, 1}):
        print("❌ Target deve essere 0 o 1")
        return False
    
    print("✅ Dataset valido!")
    return True


if __name__ == "__main__":
    build_dataset()
    verify_dataset()
