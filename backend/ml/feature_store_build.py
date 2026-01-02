from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Tuple, List, Any

from sqlalchemy import text
from app.database import engine

SURFACES = ("Hard", "Clay", "Grass")
BASE_ELO = 1500.0
K = 32.0

# Batch sizes (tuning)
FEATURES_BATCH = 2000
STATE_BATCH = 5000


def expected_score(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))


def mean_last(dq: deque, n: int) -> float:
    if not dq:
        return 0.0
    tail = list(dq)[-n:]
    return float(sum(tail)) / float(len(tail)) if tail else 0.0


def load_states():
    # surface state: (player_id, surface) -> (elo, matches_cnt, wins_cnt)
    surface_state: Dict[Tuple[int, str], Tuple[float, int, int]] = {}
    # form state: player_id -> deque([0/1], maxlen=10)
    form_state: Dict[int, deque] = {}
    # h2h wins: (player_id, opponent_id) -> wins
    h2h: Dict[Tuple[int, int], int] = {}

    with engine.connect() as conn:
        for r in conn.execute(text("""
            SELECT player_id, surface, elo, matches_cnt, wins_cnt
            FROM player_surface_state
        """)):
            surface_state[(r.player_id, r.surface)] = (float(r.elo), int(r.matches_cnt), int(r.wins_cnt))

        for r in conn.execute(text("""
            SELECT player_id, last_results
            FROM player_form_state
        """)):
            dq = deque((int(x) for x in r.last_results), maxlen=10)
            form_state[int(r.player_id)] = dq

        # h2h can be large, but for ATP-sized dataset it's manageable.
        # If it grows too much, we can switch to on-demand caching.
        for r in conn.execute(text("""
            SELECT player_id, opponent_id, wins
            FROM h2h_state
        """)):
            h2h[(int(r.player_id), int(r.opponent_id))] = int(r.wins)

    return surface_state, form_state, h2h


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


def insert_features(conn, rows: List[Dict[str, Any]]):
    if not rows:
        return
    conn.execute(
        text("""
            INSERT INTO player_match_features (
              match_id, player_id, opponent_id, match_date, surface,
              elo, recent_5, recent_10, surface_wr, h2h_wins, rank
            )
            VALUES (
              :match_id, :player_id, :opponent_id, :match_date, :surface,
              :elo, :recent_5, :recent_10, :surface_wr, :h2h_wins, :rank
            )
            ON CONFLICT (match_id, player_id) DO NOTHING
        """),
        rows,
    )


def get_resume_cursor() -> Tuple[str, int]:
    """
    Return (last_date, last_match_id) processed in feature store.
    """
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT match_date, match_id
            FROM player_match_features
            ORDER BY match_date DESC, match_id DESC
            LIMIT 1
        """)).fetchone()

    if not row:
        # start from the beginning
        return ("0001-01-01", 0)

    return (row.match_date.isoformat(), int(row.match_id))


def build_feature_store():
    surface_state, form_state, h2h = load_states()
    last_date, last_id = get_resume_cursor()

    print(f"▶ Resume from > ({last_date}, {last_id})")

    # Fetch only not-yet-processed matches (by date/id cursor)
    matches_sql = text("""
        SELECT id, match_date, surface, winner_id, loser_id, winner_rank, loser_rank
        FROM matches
        WHERE surface IN ('Hard', 'Clay', 'Grass')
          AND (match_date > :d OR (match_date = :d AND id > :id))
        ORDER BY match_date ASC, id ASC
    """)

    features_buffer: List[Dict[str, Any]] = []
    surface_state_dirty: Dict[Tuple[int, str], Tuple[float, int, int]] = {}
    form_state_dirty: Dict[int, deque] = {}
    h2h_dirty: Dict[Tuple[int, int], int] = {}

    processed = 0

    with engine.connect().execution_options(stream_results=True) as conn_stream:
        result = conn_stream.execute(matches_sql, {"d": last_date, "id": last_id})

        for m in result:
            match_id = int(m.id)
            match_date = m.match_date
            surface = m.surface

            A = int(m.winner_id)
            B = int(m.loser_id)
            rank_A = int(m.winner_rank) if m.winner_rank is not None else None
            rank_B = int(m.loser_rank) if m.loser_rank is not None else None

            # --- PRE-MATCH states (A) ---
            elo_A, mcnt_A, wcnt_A = surface_state.get((A, surface), (BASE_ELO, 0, 0))
            dq_A = form_state.get(A) or deque([], maxlen=10)
            h2h_A = h2h.get((A, B), 0)

            recent5_A = mean_last(dq_A, 5)
            recent10_A = mean_last(dq_A, 10)
            surf_wr_A = (wcnt_A / mcnt_A) if mcnt_A > 0 else 0.0

            # --- PRE-MATCH states (B) ---
            elo_B, mcnt_B, wcnt_B = surface_state.get((B, surface), (BASE_ELO, 0, 0))
            dq_B = form_state.get(B) or deque([], maxlen=10)
            h2h_B = h2h.get((B, A), 0)

            recent5_B = mean_last(dq_B, 5)
            recent10_B = mean_last(dq_B, 10)
            surf_wr_B = (wcnt_B / mcnt_B) if mcnt_B > 0 else 0.0

            # --- Write PRE-MATCH features (two rows) ---
            features_buffer.append({
                "match_id": match_id,
                "player_id": A,
                "opponent_id": B,
                "match_date": match_date,
                "surface": surface,
                "elo": float(elo_A),
                "recent_5": float(recent5_A),
                "recent_10": float(recent10_A),
                "surface_wr": float(surf_wr_A),
                "h2h_wins": int(h2h_A),
                "rank": rank_A
            })
            features_buffer.append({
                "match_id": match_id,
                "player_id": B,
                "opponent_id": A,
                "match_date": match_date,
                "surface": surface,
                "elo": float(elo_B),
                "recent_5": float(recent5_B),
                "recent_10": float(recent10_B),
                "surface_wr": float(surf_wr_B),
                "h2h_wins": int(h2h_B),
                "rank": rank_B
            })

            # --- Update Elo (post-match) on that surface ---
            exp_A = expected_score(elo_A, elo_B)
            exp_B = 1.0 - exp_A

            elo_A_new = elo_A + K * (1.0 - exp_A)
            elo_B_new = elo_B + K * (0.0 - exp_B)

            # Update surface stats
            mcnt_A_new = mcnt_A + 1
            wcnt_A_new = wcnt_A + 1
            mcnt_B_new = mcnt_B + 1
            wcnt_B_new = wcnt_B + 0

            surface_state[(A, surface)] = (float(elo_A_new), int(mcnt_A_new), int(wcnt_A_new))
            surface_state[(B, surface)] = (float(elo_B_new), int(mcnt_B_new), int(wcnt_B_new))
            surface_state_dirty[(A, surface)] = surface_state[(A, surface)]
            surface_state_dirty[(B, surface)] = surface_state[(B, surface)]

            # Update form (last 10 results)
            dq_A.append(1)
            dq_B.append(0)
            form_state[A] = dq_A
            form_state[B] = dq_B
            form_state_dirty[A] = dq_A
            form_state_dirty[B] = dq_B

            # Update H2H
            h2h[(A, B)] = h2h_A + 1
            h2h_dirty[(A, B)] = h2h[(A, B)]

            processed += 1

            # --- Flush periodically ---
            if len(features_buffer) >= FEATURES_BATCH:
                with engine.begin() as conn:
                    insert_features(conn, features_buffer)
                features_buffer.clear()

            if len(surface_state_dirty) + len(form_state_dirty) + len(h2h_dirty) >= STATE_BATCH:
                flush_states(surface_state_dirty, form_state_dirty, h2h_dirty)

        # final flush
        if features_buffer:
            with engine.begin() as conn:
                insert_features(conn, features_buffer)
            features_buffer.clear()

        flush_states(surface_state_dirty, form_state_dirty, h2h_dirty)

    print(f"✅ Feature store aggiornato. Match processati: {processed}")


def flush_states(
    surface_dirty: Dict[Tuple[int, str], Tuple[float, int, int]],
    form_dirty: Dict[int, deque],
    h2h_dirty: Dict[Tuple[int, int], int],
):
    if not surface_dirty and not form_dirty and not h2h_dirty:
        return

    surface_rows = [
        {"player_id": pid, "surface": surf, "elo": elo, "matches_cnt": mcnt, "wins_cnt": wcnt}
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

    with engine.begin() as conn:
        upsert_surface_state(conn, surface_rows)
        upsert_form_state(conn, form_rows)
        upsert_h2h_state(conn, h2h_rows)

    surface_dirty.clear()
    form_dirty.clear()
    h2h_dirty.clear()


if __name__ == "__main__":
    build_feature_store()
