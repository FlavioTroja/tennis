from collections import deque
from sqlalchemy import text
from app.database import engine

BASE_ELO = 1500.0


def get_player_id(name: str) -> int:
    with engine.connect() as conn:
        pid = conn.execute(
            text("SELECT id FROM players WHERE name = :n"),
            {"n": name}
        ).scalar()
    if pid is None:
        raise ValueError(f"Giocatore non trovato: {name}")
    return int(pid)


def get_surface_state(pid: int, surface: str):
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
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT last_results
            FROM player_form_state
            WHERE player_id = :pid
        """), {"pid": pid}).fetchone()

    if not r or not r.last_results:
        return 0.0, 0.0

    # Converti UNA VOLTA
    results = list(r.last_results)

    last_5 = results[-5:]
    last_10 = results[-10:]

    recent_5 = sum(last_5) / len(last_5)
    recent_10 = sum(last_10) / len(last_10)

    return float(recent_5), float(recent_10)



def get_h2h(a: int, b: int) -> int:
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT wins FROM h2h_state
            WHERE player_id = :a AND opponent_id = :b
        """), {"a": a, "b": b}).scalar()
    return int(r) if r else 0


def get_latest_rank(pid: int) -> int:
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT rank
            FROM player_match_features
            WHERE player_id = :pid AND rank IS NOT NULL
            ORDER BY match_date DESC
            LIMIT 1
        """), {"pid": pid}).scalar()
    if r is None:
        raise ValueError("Ranking non disponibile")
    return int(r)
