"""
Tennis Feature Service
=======================
Funzioni per recuperare feature dal feature store per predizioni live.
"""

from datetime import date, timedelta
from sqlalchemy import text
from app.database import engine

BASE_ELO = 1500.0


def get_player_id(name: str) -> int:
    """Ottiene l'ID di un giocatore dal nome."""
    with engine.connect() as conn:
        pid = conn.execute(
            text("SELECT id FROM players WHERE name = :n"),
            {"n": name}
        ).scalar()
    if pid is None:
        raise ValueError(f"Giocatore non trovato: {name}")
    return int(pid)


def get_surface_state(pid: int, surface: str):
    """Ritorna (elo, surface_win_rate) per un giocatore su una superficie."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT elo, matches_cnt, wins_cnt
            FROM player_surface_state
            WHERE player_id = :pid AND surface = :surface
        """), {"pid": pid, "surface": surface}).fetchone()

    if not r:
        return BASE_ELO, 0.0

    elo, mcnt, wcnt = r
    wr = (wcnt / mcnt) if mcnt > 0 else 0.0
    return float(elo), float(wr)


def get_form(pid: int):
    """Ritorna (recent_5, recent_10) win rates."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT last_results
            FROM player_form_state
            WHERE player_id = :pid
        """), {"pid": pid}).fetchone()

    if not r or not r.last_results:
        return 0.0, 0.0

    results = list(r.last_results)
    last_5 = results[-5:] if len(results) >= 5 else results
    last_10 = results[-10:] if len(results) >= 10 else results

    recent_5 = sum(last_5) / len(last_5) if last_5 else 0.0
    recent_10 = sum(last_10) / len(last_10) if last_10 else 0.0

    return float(recent_5), float(recent_10)


def get_h2h(a: int, b: int) -> int:
    """Ritorna numero di vittorie di a contro b."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT wins FROM h2h_state
            WHERE player_id = :a AND opponent_id = :b
        """), {"a": a, "b": b}).scalar()
    return int(r) if r else 0


def get_latest_rank(pid: int) -> int:
    """Ritorna l'ultimo ranking noto."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT rank
            FROM player_match_features
            WHERE player_id = :pid AND rank IS NOT NULL
            ORDER BY match_date DESC
            LIMIT 1
        """), {"pid": pid}).scalar()
    if r is None:
        return 500  # Default se non disponibile
    return int(r)


def get_days_since_last_match(pid: int) -> int:
    """Ritorna giorni dall'ultimo match."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT last_match_date
            FROM player_activity_state
            WHERE player_id = :pid
        """), {"pid": pid}).scalar()
    
    if r is None:
        return 7  # Default: una settimana
    
    days = (date.today() - r).days
    return max(0, days)


def get_player_age(pid: int) -> float:
    """Ritorna l'età del giocatore."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT birth_date
            FROM players
            WHERE id = :pid
        """), {"pid": pid}).scalar()
    
    if r is None:
        return 25.0  # Default
    
    age = (date.today() - r).days / 365.25
    return round(age, 1)


def get_matches_last_30_days(pid: int) -> int:
    """Ritorna numero di match negli ultimi 30 giorni."""
    cutoff = date.today() - timedelta(days=30)
    
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT COUNT(*)
            FROM player_match_features
            WHERE player_id = :pid AND match_date >= :cutoff
        """), {"pid": pid, "cutoff": cutoff}).scalar()
    
    return int(r) if r else 0


def get_serve_stats(pid: int):
    """Ritorna statistiche servizio aggregate."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT ace_total, df_total, svpt_total,
                   first_in_total, first_won_total, second_won_total,
                   bp_faced_total, bp_saved_total
            FROM player_serve_state
            WHERE player_id = :pid
        """), {"pid": pid}).fetchone()
    
    if not r or not r.svpt_total or r.svpt_total == 0:
        return {
            "ace_pct": 0.0,
            "df_pct": 0.0,
            "first_serve_pct": 0.0,
            "first_won_pct": 0.0,
            "bp_save_pct": 0.0,
        }
    
    svpt = r.svpt_total
    first_in = r.first_in_total or 0
    
    return {
        "ace_pct": (r.ace_total or 0) / svpt,
        "df_pct": (r.df_total or 0) / svpt,
        "first_serve_pct": first_in / svpt if svpt > 0 else 0.0,
        "first_won_pct": (r.first_won_total or 0) / first_in if first_in > 0 else 0.0,
        "bp_save_pct": (r.bp_saved_total or 0) / (r.bp_faced_total or 1),
    }


def get_level_experience(pid: int, level: str) -> float:
    """Ritorna win rate per un livello torneo specifico."""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT matches_cnt, wins_cnt
            FROM player_level_state
            WHERE player_id = :pid AND level = :level
        """), {"pid": pid, "level": level}).fetchone()
    
    if not r or not r.matches_cnt or r.matches_cnt == 0:
        return 0.0
    
    return r.wins_cnt / r.matches_cnt
