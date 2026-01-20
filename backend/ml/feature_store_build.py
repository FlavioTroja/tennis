"""
Tennis Feature Store Builder
=============================
Costruisce e mantiene il feature store per le predizioni ML.

Feature calcolate per ogni giocatore PRE-MATCH:
- Elo rating per superficie
- Win rate su superficie
- Form recente (ultimi 5 e 10 match)
- Head-to-head
- Fatigue (giorni dall'ultimo match)
- Età
- Match giocati negli ultimi 30 giorni
- Statistiche servizio (ace%, df%, 1st serve %, bp saved %)
- Esperienza tournament level (% vittorie per livello)
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import date, timedelta
from typing import Dict, Tuple, List, Any, Optional

from sqlalchemy import text
from app.database import engine

SURFACES = ("Hard", "Clay", "Grass")
TOURNAMENT_LEVELS = ("G", "M", "A", "B", "C", "D", "F")  # Grand Slam, Masters, etc.
BASE_ELO = 1500.0
K = 32.0

# Batch sizes
FEATURES_BATCH = 2000
STATE_BATCH = 5000


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def expected_score(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))


def mean_last(dq: deque, n: int) -> float:
    if not dq:
        return 0.0
    tail = list(dq)[-n:]
    return float(sum(tail)) / float(len(tail)) if tail else 0.0


def safe_ratio(numerator: int, denominator: int, default: float = 0.0) -> float:
    """Calcola ratio evitando divisione per zero."""
    if denominator is None or denominator == 0:
        return default
    if numerator is None:
        return default
    return float(numerator) / float(denominator)


# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def load_states():
    """Carica stati esistenti dal database."""
    
    # surface state: (player_id, surface) -> (elo, matches_cnt, wins_cnt)
    surface_state: Dict[Tuple[int, str], Tuple[float, int, int]] = {}
    # form state: player_id -> deque([0/1], maxlen=10)
    form_state: Dict[int, deque] = {}
    # h2h wins: (player_id, opponent_id) -> wins
    h2h: Dict[Tuple[int, int], int] = {}
    # last match date: player_id -> date
    last_match: Dict[int, date] = {}
    # matches last 30 days: player_id -> list of match dates
    recent_matches: Dict[int, List[date]] = defaultdict(list)
    # serve stats: player_id -> {ace_total, df_total, svpt_total, 1stIn_total, ...}
    serve_stats: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    # tournament level experience: (player_id, level) -> (matches, wins)
    level_exp: Dict[Tuple[int, str], Tuple[int, int]] = {}

    with engine.connect() as conn:
        # Surface state
        try:
            for r in conn.execute(text("""
                SELECT player_id, surface, elo, matches_cnt, wins_cnt
                FROM player_surface_state
            """)):
                surface_state[(r.player_id, r.surface)] = (
                    float(r.elo), int(r.matches_cnt), int(r.wins_cnt)
                )
        except Exception:
            pass  # Tabella non esiste ancora

        # Form state
        try:
            for r in conn.execute(text("""
                SELECT player_id, last_results
                FROM player_form_state
            """)):
                dq = deque((int(x) for x in r.last_results), maxlen=10)
                form_state[int(r.player_id)] = dq
        except Exception:
            pass

        # H2H
        try:
            for r in conn.execute(text("""
                SELECT player_id, opponent_id, wins
                FROM h2h_state
            """)):
                h2h[(int(r.player_id), int(r.opponent_id))] = int(r.wins)
        except Exception:
            pass

        # Last match date
        try:
            for r in conn.execute(text("""
                SELECT player_id, last_match_date
                FROM player_activity_state
            """)):
                last_match[int(r.player_id)] = r.last_match_date
        except Exception:
            pass

        # Serve stats
        try:
            for r in conn.execute(text("""
                SELECT player_id, ace_total, df_total, svpt_total, 
                       first_in_total, first_won_total, second_won_total,
                       bp_faced_total, bp_saved_total
                FROM player_serve_state
            """)):
                serve_stats[int(r.player_id)] = {
                    "ace": int(r.ace_total or 0),
                    "df": int(r.df_total or 0),
                    "svpt": int(r.svpt_total or 0),
                    "1stIn": int(r.first_in_total or 0),
                    "1stWon": int(r.first_won_total or 0),
                    "2ndWon": int(r.second_won_total or 0),
                    "bpFaced": int(r.bp_faced_total or 0),
                    "bpSaved": int(r.bp_saved_total or 0),
                }
        except Exception:
            pass

        # Tournament level experience
        try:
            for r in conn.execute(text("""
                SELECT player_id, level, matches_cnt, wins_cnt
                FROM player_level_state
            """)):
                level_exp[(int(r.player_id), r.level)] = (
                    int(r.matches_cnt), int(r.wins_cnt)
                )
        except Exception:
            pass

    return surface_state, form_state, h2h, last_match, recent_matches, serve_stats, level_exp


# =============================================================================
# UPSERT FUNCTIONS
# =============================================================================

def upsert_surface_state(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_surface_state (player_id, surface, elo, matches_cnt, wins_cnt)
            VALUES (:player_id, :surface, :elo, :matches_cnt, :wins_cnt)
            ON CONFLICT (player_id, surface) DO UPDATE
            SET elo = EXCLUDED.elo,
                matches_cnt = EXCLUDED.matches_cnt,
                wins_cnt = EXCLUDED.wins_cnt
        """),
        rows,
    )


def upsert_form_state(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_form_state (player_id, last_results)
            VALUES (:player_id, :last_results)
            ON CONFLICT (player_id) DO UPDATE
            SET last_results = EXCLUDED.last_results
        """),
        rows,
    )


def upsert_h2h_state(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO h2h_state (player_id, opponent_id, wins)
            VALUES (:player_id, :opponent_id, :wins)
            ON CONFLICT (player_id, opponent_id) DO UPDATE
            SET wins = EXCLUDED.wins
        """),
        rows,
    )


def upsert_activity_state(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_activity_state (player_id, last_match_date)
            VALUES (:player_id, :last_match_date)
            ON CONFLICT (player_id) DO UPDATE
            SET last_match_date = EXCLUDED.last_match_date
        """),
        rows,
    )


def upsert_serve_state(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_serve_state (
                player_id, ace_total, df_total, svpt_total,
                first_in_total, first_won_total, second_won_total,
                bp_faced_total, bp_saved_total
            )
            VALUES (
                :player_id, :ace_total, :df_total, :svpt_total,
                :first_in_total, :first_won_total, :second_won_total,
                :bp_faced_total, :bp_saved_total
            )
            ON CONFLICT (player_id) DO UPDATE
            SET ace_total = EXCLUDED.ace_total,
                df_total = EXCLUDED.df_total,
                svpt_total = EXCLUDED.svpt_total,
                first_in_total = EXCLUDED.first_in_total,
                first_won_total = EXCLUDED.first_won_total,
                second_won_total = EXCLUDED.second_won_total,
                bp_faced_total = EXCLUDED.bp_faced_total,
                bp_saved_total = EXCLUDED.bp_saved_total
        """),
        rows,
    )


def upsert_level_state(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_level_state (player_id, level, matches_cnt, wins_cnt)
            VALUES (:player_id, :level, :matches_cnt, :wins_cnt)
            ON CONFLICT (player_id, level) DO UPDATE
            SET matches_cnt = EXCLUDED.matches_cnt,
                wins_cnt = EXCLUDED.wins_cnt
        """),
        rows,
    )


def insert_features(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_match_features (
              match_id, player_id, opponent_id, match_date, surface,
              elo, recent_5, recent_10, surface_wr, h2h_wins, rank,
              days_since_last_match, age, matches_last_30d,
              ace_pct, df_pct, first_serve_pct, first_serve_won_pct,
              second_serve_won_pct, bp_save_pct,
              level_win_rate
            )
            VALUES (
              :match_id, :player_id, :opponent_id, :match_date, :surface,
              :elo, :recent_5, :recent_10, :surface_wr, :h2h_wins, :rank,
              :days_since_last_match, :age, :matches_last_30d,
              :ace_pct, :df_pct, :first_serve_pct, :first_serve_won_pct,
              :second_serve_won_pct, :bp_save_pct,
              :level_win_rate
            )
            ON CONFLICT (match_id, player_id) DO NOTHING
        """),
        rows,
    )


# =============================================================================
# SCHEMA CREATION
# =============================================================================

def create_tables():
    """Crea le tabelle necessarie se non esistono."""
    
    with engine.begin() as conn:
        # Tabella feature principali
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_match_features (
                match_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                opponent_id INTEGER NOT NULL,
                match_date DATE NOT NULL,
                surface VARCHAR(10),
                elo FLOAT,
                recent_5 FLOAT,
                recent_10 FLOAT,
                surface_wr FLOAT,
                h2h_wins INTEGER,
                rank INTEGER,
                days_since_last_match INTEGER,
                age FLOAT,
                matches_last_30d INTEGER,
                ace_pct FLOAT,
                df_pct FLOAT,
                first_serve_pct FLOAT,
                first_serve_won_pct FLOAT,
                second_serve_won_pct FLOAT,
                bp_save_pct FLOAT,
                level_win_rate FLOAT,
                PRIMARY KEY (match_id, player_id)
            )
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pmf_date ON player_match_features(match_date)
        """))
        
        # Tabelle stato
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_surface_state (
                player_id INTEGER NOT NULL,
                surface VARCHAR(10) NOT NULL,
                elo FLOAT,
                matches_cnt INTEGER,
                wins_cnt INTEGER,
                PRIMARY KEY (player_id, surface)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_form_state (
                player_id INTEGER PRIMARY KEY,
                last_results INTEGER[]
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS h2h_state (
                player_id INTEGER NOT NULL,
                opponent_id INTEGER NOT NULL,
                wins INTEGER,
                PRIMARY KEY (player_id, opponent_id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_activity_state (
                player_id INTEGER PRIMARY KEY,
                last_match_date DATE
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_serve_state (
                player_id INTEGER PRIMARY KEY,
                ace_total INTEGER DEFAULT 0,
                df_total INTEGER DEFAULT 0,
                svpt_total INTEGER DEFAULT 0,
                first_in_total INTEGER DEFAULT 0,
                first_won_total INTEGER DEFAULT 0,
                second_won_total INTEGER DEFAULT 0,
                bp_faced_total INTEGER DEFAULT 0,
                bp_saved_total INTEGER DEFAULT 0
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS player_level_state (
                player_id INTEGER NOT NULL,
                level VARCHAR(1) NOT NULL,
                matches_cnt INTEGER DEFAULT 0,
                wins_cnt INTEGER DEFAULT 0,
                PRIMARY KEY (player_id, level)
            )
        """))
    
    print("✅ Tabelle create/verificate")


# =============================================================================
# FEATURE CALCULATION
# =============================================================================

def calculate_serve_percentages(stats: Dict[str, int]) -> Dict[str, float]:
    """Calcola percentuali servizio dai totali."""
    svpt = stats.get("svpt", 0)
    first_in = stats.get("1stIn", 0)
    
    return {
        "ace_pct": safe_ratio(stats.get("ace", 0), svpt),
        "df_pct": safe_ratio(stats.get("df", 0), svpt),
        "first_serve_pct": safe_ratio(first_in, svpt),
        "first_serve_won_pct": safe_ratio(stats.get("1stWon", 0), first_in),
        "second_serve_won_pct": safe_ratio(
            stats.get("2ndWon", 0), 
            svpt - first_in if svpt > first_in else 0
        ),
        "bp_save_pct": safe_ratio(
            stats.get("bpSaved", 0), 
            stats.get("bpFaced", 0)
        ),
    }


def get_resume_cursor() -> Tuple[str, int]:
    """Ritorna l'ultimo match processato."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT match_date, match_id
            FROM player_match_features
            ORDER BY match_date DESC, match_id DESC
            LIMIT 1
        """)).fetchone()

    if not row:
        return ("0001-01-01", 0)

    return (row.match_date.isoformat(), int(row.match_id))


# =============================================================================
# MAIN BUILD FUNCTION
# =============================================================================

def build_feature_store():
    """Costruisce/aggiorna il feature store."""
    
    print("=" * 60)
    print("🎾 FEATURE STORE BUILDER")
    print("=" * 60)
    
    # Crea tabelle se necessario
    create_tables()
    
    # Carica stati esistenti
    print("\n📂 Caricamento stati...")
    (surface_state, form_state, h2h, last_match, 
     recent_matches, serve_stats, level_exp) = load_states()
    
    last_date, last_id = get_resume_cursor()
    print(f"▶ Resume from > ({last_date}, {last_id})")

    # Query match con tutti i nuovi campi
    matches_sql = text("""
        SELECT 
            m.id, m.match_date, m.surface, m.tournament_level,
            m.winner_id, m.loser_id, 
            m.winner_rank, m.loser_rank,
            m.winner_age, m.loser_age,
            m.w_ace, m.w_df, m.w_svpt, m.w_1stIn, m.w_1stWon, m.w_2ndWon,
            m.w_bpFaced, m.w_bpSaved,
            m.l_ace, m.l_df, m.l_svpt, m.l_1stIn, m.l_1stWon, m.l_2ndWon,
            m.l_bpFaced, m.l_bpSaved
        FROM matches m
        WHERE m.surface IN ('Hard', 'Clay', 'Grass')
          AND (m.match_date > :d OR (m.match_date = :d AND m.id > :id))
        ORDER BY m.match_date ASC, m.id ASC
    """)

    features_buffer: List[Dict[str, Any]] = []
    
    # Dirty state tracking
    surface_dirty: Dict[Tuple[int, str], Tuple[float, int, int]] = {}
    form_dirty: Dict[int, deque] = {}
    h2h_dirty: Dict[Tuple[int, int], int] = {}
    activity_dirty: Dict[int, date] = {}
    serve_dirty: Dict[int, Dict[str, int]] = {}
    level_dirty: Dict[Tuple[int, str], Tuple[int, int]] = {}

    processed = 0

    with engine.connect().execution_options(stream_results=True) as conn_stream:
        result = conn_stream.execute(matches_sql, {"d": last_date, "id": last_id})

        for m in result:
            match_id = int(m.id)
            match_date = m.match_date
            surface = m.surface
            level = m.tournament_level or "A"

            A = int(m.winner_id)  # Winner
            B = int(m.loser_id)   # Loser
            
            rank_A = int(m.winner_rank) if m.winner_rank else None
            rank_B = int(m.loser_rank) if m.loser_rank else None
            
            age_A = float(m.winner_age) if m.winner_age else None
            age_B = float(m.loser_age) if m.loser_age else None

            # === PRE-MATCH FEATURE: Player A (Winner) ===
            elo_A, mcnt_A, wcnt_A = surface_state.get((A, surface), (BASE_ELO, 0, 0))
            dq_A = form_state.get(A) or deque([], maxlen=10)
            h2h_A = h2h.get((A, B), 0)
            last_A = last_match.get(A)
            days_since_A = (match_date - last_A).days if last_A else None
            matches_30d_A = len([d for d in recent_matches.get(A, []) 
                                if (match_date - d).days <= 30])
            serve_pct_A = calculate_serve_percentages(serve_stats.get(A, {}))
            level_m_A, level_w_A = level_exp.get((A, level), (0, 0))
            level_wr_A = safe_ratio(level_w_A, level_m_A)

            # === PRE-MATCH FEATURE: Player B (Loser) ===
            elo_B, mcnt_B, wcnt_B = surface_state.get((B, surface), (BASE_ELO, 0, 0))
            dq_B = form_state.get(B) or deque([], maxlen=10)
            h2h_B = h2h.get((B, A), 0)
            last_B = last_match.get(B)
            days_since_B = (match_date - last_B).days if last_B else None
            matches_30d_B = len([d for d in recent_matches.get(B, []) 
                                if (match_date - d).days <= 30])
            serve_pct_B = calculate_serve_percentages(serve_stats.get(B, {}))
            level_m_B, level_w_B = level_exp.get((B, level), (0, 0))
            level_wr_B = safe_ratio(level_w_B, level_m_B)

            # === WRITE PRE-MATCH FEATURES ===
            features_buffer.append({
                "match_id": match_id,
                "player_id": A,
                "opponent_id": B,
                "match_date": match_date,
                "surface": surface,
                "elo": float(elo_A),
                "recent_5": mean_last(dq_A, 5),
                "recent_10": mean_last(dq_A, 10),
                "surface_wr": safe_ratio(wcnt_A, mcnt_A),
                "h2h_wins": int(h2h_A),
                "rank": rank_A,
                "days_since_last_match": days_since_A,
                "age": age_A,
                "matches_last_30d": matches_30d_A,
                **serve_pct_A,
                "level_win_rate": level_wr_A,
            })
            
            features_buffer.append({
                "match_id": match_id,
                "player_id": B,
                "opponent_id": A,
                "match_date": match_date,
                "surface": surface,
                "elo": float(elo_B),
                "recent_5": mean_last(dq_B, 5),
                "recent_10": mean_last(dq_B, 10),
                "surface_wr": safe_ratio(wcnt_B, mcnt_B),
                "h2h_wins": int(h2h_B),
                "rank": rank_B,
                "days_since_last_match": days_since_B,
                "age": age_B,
                "matches_last_30d": matches_30d_B,
                **serve_pct_B,
                "level_win_rate": level_wr_B,
            })

            # === UPDATE STATES (POST-MATCH) ===
            
            # Elo update
            exp_A = expected_score(elo_A, elo_B)
            elo_A_new = elo_A + K * (1.0 - exp_A)
            elo_B_new = elo_B + K * (0.0 - (1.0 - exp_A))

            surface_state[(A, surface)] = (elo_A_new, mcnt_A + 1, wcnt_A + 1)
            surface_state[(B, surface)] = (elo_B_new, mcnt_B + 1, wcnt_B)
            surface_dirty[(A, surface)] = surface_state[(A, surface)]
            surface_dirty[(B, surface)] = surface_state[(B, surface)]

            # Form update
            dq_A.append(1)
            dq_B.append(0)
            form_state[A] = dq_A
            form_state[B] = dq_B
            form_dirty[A] = dq_A
            form_dirty[B] = dq_B

            # H2H update
            h2h[(A, B)] = h2h_A + 1
            h2h_dirty[(A, B)] = h2h[(A, B)]

            # Activity update
            last_match[A] = match_date
            last_match[B] = match_date
            activity_dirty[A] = match_date
            activity_dirty[B] = match_date
            
            # Recent matches update
            recent_matches[A].append(match_date)
            recent_matches[B].append(match_date)
            # Keep only last 60 days
            cutoff = match_date - timedelta(days=60)
            recent_matches[A] = [d for d in recent_matches[A] if d > cutoff]
            recent_matches[B] = [d for d in recent_matches[B] if d > cutoff]

            # Serve stats update (if available)
            if m.w_svpt:
                ss = serve_stats[A]
                ss["ace"] += m.w_ace or 0
                ss["df"] += m.w_df or 0
                ss["svpt"] += m.w_svpt or 0
                ss["1stIn"] += m.w_1stIn or 0
                ss["1stWon"] += m.w_1stWon or 0
                ss["2ndWon"] += m.w_2ndWon or 0
                ss["bpFaced"] += m.w_bpFaced or 0
                ss["bpSaved"] += m.w_bpSaved or 0
                serve_dirty[A] = ss
                
            if m.l_svpt:
                ss = serve_stats[B]
                ss["ace"] += m.l_ace or 0
                ss["df"] += m.l_df or 0
                ss["svpt"] += m.l_svpt or 0
                ss["1stIn"] += m.l_1stIn or 0
                ss["1stWon"] += m.l_1stWon or 0
                ss["2ndWon"] += m.l_2ndWon or 0
                ss["bpFaced"] += m.l_bpFaced or 0
                ss["bpSaved"] += m.l_bpSaved or 0
                serve_dirty[B] = ss

            # Level experience update
            level_exp[(A, level)] = (level_m_A + 1, level_w_A + 1)
            level_exp[(B, level)] = (level_m_B + 1, level_w_B)
            level_dirty[(A, level)] = level_exp[(A, level)]
            level_dirty[(B, level)] = level_exp[(B, level)]

            processed += 1

            # Flush periodically
            if len(features_buffer) >= FEATURES_BATCH:
                with engine.begin() as conn:
                    insert_features(conn, features_buffer)
                features_buffer.clear()
                print(f"   Processati {processed} match...")

            if (len(surface_dirty) + len(form_dirty) + len(h2h_dirty) + 
                len(activity_dirty) + len(serve_dirty) + len(level_dirty)) >= STATE_BATCH:
                flush_all_states(
                    surface_dirty, form_dirty, h2h_dirty,
                    activity_dirty, serve_dirty, level_dirty
                )

        # Final flush
        if features_buffer:
            with engine.begin() as conn:
                insert_features(conn, features_buffer)
            features_buffer.clear()

        flush_all_states(
            surface_dirty, form_dirty, h2h_dirty,
            activity_dirty, serve_dirty, level_dirty
        )

    print(f"\n✅ Feature store aggiornato. Match processati: {processed}")


def flush_all_states(surface_dirty, form_dirty, h2h_dirty, 
                     activity_dirty, serve_dirty, level_dirty):
    """Flush tutti gli stati dirty al database."""
    
    if not any([surface_dirty, form_dirty, h2h_dirty, 
                activity_dirty, serve_dirty, level_dirty]):
        return

    surface_rows = [
        {"player_id": pid, "surface": surf, "elo": elo, 
         "matches_cnt": mcnt, "wins_cnt": wcnt}
        for (pid, surf), (elo, mcnt, wcnt) in surface_dirty.items()
    ]
    
    form_rows = [
        {"player_id": pid, "last_results": list(dq)}
        for pid, dq in form_dirty.items()
    ]
    
    h2h_rows = [
        {"player_id": a, "opponent_id": b, "wins": wins}
        for (a, b), wins in h2h_dirty.items()
    ]
    
    activity_rows = [
        {"player_id": pid, "last_match_date": dt}
        for pid, dt in activity_dirty.items()
    ]
    
    serve_rows = [
        {
            "player_id": pid,
            "ace_total": ss["ace"],
            "df_total": ss["df"],
            "svpt_total": ss["svpt"],
            "first_in_total": ss["1stIn"],
            "first_won_total": ss["1stWon"],
            "second_won_total": ss["2ndWon"],
            "bp_faced_total": ss["bpFaced"],
            "bp_saved_total": ss["bpSaved"],
        }
        for pid, ss in serve_dirty.items()
    ]
    
    level_rows = [
        {"player_id": pid, "level": lvl, "matches_cnt": m, "wins_cnt": w}
        for (pid, lvl), (m, w) in level_dirty.items()
    ]

    with engine.begin() as conn:
        upsert_surface_state(conn, surface_rows)
        upsert_form_state(conn, form_rows)
        upsert_h2h_state(conn, h2h_rows)
        upsert_activity_state(conn, activity_rows)
        upsert_serve_state(conn, serve_rows)
        upsert_level_state(conn, level_rows)

    surface_dirty.clear()
    form_dirty.clear()
    h2h_dirty.clear()
    activity_dirty.clear()
    serve_dirty.clear()
    level_dirty.clear()


if __name__ == "__main__":
    build_feature_store()
