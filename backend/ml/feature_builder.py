"""
Tennis Match Prediction - Feature Builder
==========================================
Costruisce feature per match live usando il feature store.
Usato dalla odds pipeline per calcolare feature pre-match.
"""

import pandas as pd
from sqlalchemy import text
from app.database import engine

DEFAULT_ELO = 1500.0


def get_surface_state(player_id: int, surface: str):
    """
    Ritorna (elo, surface_win_rate) dal feature store.
    """
    query = text("""
        SELECT elo, matches_cnt, wins_cnt
        FROM player_surface_state
        WHERE player_id = :pid AND surface = :surface
    """)
    
    try:
        with engine.connect() as conn:
            r = conn.execute(query, {"pid": player_id, "surface": surface}).fetchone()
        
        if r:
            elo = float(r.elo)
            wr = (r.wins_cnt / r.matches_cnt) if r.matches_cnt > 0 else 0.0
            return elo, float(wr)
    except Exception:
        pass
    
    return DEFAULT_ELO, 0.0


def get_form(player_id: int):
    """
    Ritorna (recent_5, recent_10) dal feature store.
    """
    query = text("""
        SELECT last_results
        FROM player_form_state
        WHERE player_id = :pid
    """)
    
    try:
        with engine.connect() as conn:
            r = conn.execute(query, {"pid": player_id}).fetchone()
        
        if r and r.last_results:
            results = list(r.last_results)
            last_5 = results[-5:] if len(results) >= 5 else results
            last_10 = results[-10:] if len(results) >= 10 else results
            
            recent_5 = sum(last_5) / len(last_5) if last_5 else 0.0
            recent_10 = sum(last_10) / len(last_10) if last_10 else 0.0
            return float(recent_5), float(recent_10)
    except Exception:
        pass
    
    return 0.0, 0.0


def get_h2h(player_id: int, opponent_id: int):
    """
    Ritorna numero vittorie H2H dal feature store.
    """
    query = text("""
        SELECT wins
        FROM h2h_state
        WHERE player_id = :pid AND opponent_id = :oid
    """)
    
    try:
        with engine.connect() as conn:
            r = conn.execute(query, {"pid": player_id, "oid": opponent_id}).scalar()
        return int(r) if r else 0
    except Exception:
        return 0


def get_latest_rank(player_id: int):
    """
    Ritorna ultimo ranking disponibile.
    """
    query = text("""
        SELECT rank
        FROM player_match_features
        WHERE player_id = :pid AND rank IS NOT NULL
        ORDER BY match_date DESC
        LIMIT 1
    """)
    
    try:
        with engine.connect() as conn:
            r = conn.execute(query, {"pid": player_id}).scalar()
        return int(r) if r else 500
    except Exception:
        return 500


def compute_player_features(player_id: int, opponent_id: int, surface: str):
    """
    Calcola tutte le feature per un giocatore.
    """
    elo, surface_wr = get_surface_state(player_id, surface)
    recent_5, recent_10 = get_form(player_id)
    h2h_wins = get_h2h(player_id, opponent_id)
    rank = get_latest_rank(player_id)
    
    return {
        "elo": elo,
        "surface_wr": surface_wr,
        "recent_5": recent_5,
        "recent_10": recent_10,
        "h2h_wins": h2h_wins,
        "rank": rank,
    }


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Costruisce feature differenziali per un DataFrame di match.
    
    Input REQUIRED columns:
    - player_a_id
    - player_b_id
    - surface
    
    Output: DataFrame con colonne feature aggiunte
    """
    
    rows = []
    
    for _, r in df.iterrows():
        # Feature giocatore A
        feat_a = compute_player_features(
            r.player_a_id,
            r.player_b_id,
            r.surface
        )
        
        # Feature giocatore B
        feat_b = compute_player_features(
            r.player_b_id,
            r.player_a_id,
            r.surface
        )
        
        # Feature differenziali
        features = {
            "elo_diff": feat_a["elo"] - feat_b["elo"],
            "ranking_diff": feat_a["rank"] - feat_b["rank"],
            "recent_5_diff": feat_a["recent_5"] - feat_b["recent_5"],
            "recent_10_diff": feat_a["recent_10"] - feat_b["recent_10"],
            "surface_diff": feat_a["surface_wr"] - feat_b["surface_wr"],
            "h2h_diff": feat_a["h2h_wins"] - feat_b["h2h_wins"],
        }
        
        rows.append({**r.to_dict(), **features})
    
    return pd.DataFrame(rows)
