from sqlalchemy import text
from app.database import engine

K = 32
BASE_ELO = 1500


def expected_score(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def build_elo():
    with engine.connect() as conn:
        matches = conn.execute(text("""
            SELECT
                match_date,
                winner_id,
                loser_id
            FROM matches
            ORDER BY match_date ASC
        """)).fetchall()

    elo = {}
    elo_history = []

    for m in matches:
        A = m.winner_id
        B = m.loser_id

        elo_A = elo.get(A, BASE_ELO)
        elo_B = elo.get(B, BASE_ELO)

        exp_A = expected_score(elo_A, elo_B)
        exp_B = expected_score(elo_B, elo_A)

        # aggiornamento Elo
        elo_A_new = elo_A + K * (1 - exp_A)
        elo_B_new = elo_B + K * (0 - exp_B)

        elo[A] = elo_A_new
        elo[B] = elo_B_new

        elo_history.append((A, m.match_date, elo_A_new))
        elo_history.append((B, m.match_date, elo_B_new))

    return elo_history
