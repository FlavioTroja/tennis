from collections import defaultdict
from sqlalchemy import text
from app.database import engine

K = 32
BASE_ELO = 1500.0


def expected_score(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def build_elo_surface():
    with engine.connect() as conn:
        matches = conn.execute(text("""
            SELECT
                id,
                match_date,
                surface,
                winner_id,
                loser_id
            FROM matches
            WHERE surface IN ('Hard', 'Clay', 'Grass')
            ORDER BY match_date ASC, id ASC
        """)).fetchall()

    # elo[player_id][surface]
    elo = defaultdict(lambda: {
        "Hard": BASE_ELO,
        "Clay": BASE_ELO,
        "Grass": BASE_ELO
    })

    rows = []

    for m in matches:
        surface = m.surface
        match_id = m.id
        match_date = m.match_date

        A = m.winner_id
        B = m.loser_id

        elo_A = elo[A][surface]
        elo_B = elo[B][surface]

        exp_A = expected_score(elo_A, elo_B)
        exp_B = expected_score(elo_B, elo_A)

        elo_A_new = elo_A + K * (1 - exp_A)
        elo_B_new = elo_B + K * (0 - exp_B)

        elo[A][surface] = elo_A_new
        elo[B][surface] = elo_B_new

        rows.append({
            "pid": A,
            "surface": surface,
            "mid": match_id,
            "date": match_date,
            "elo": elo_A_new
        })
        rows.append({
            "pid": B,
            "surface": surface,
            "mid": match_id,
            "date": match_date,
            "elo": elo_B_new
        })

    return rows


def save_to_db(rows):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM player_elo"))

        conn.execute(
            text("""
                INSERT INTO player_elo
                    (player_id, surface, match_id, match_date, elo)
                VALUES
                    (:pid, :surface, :mid, :date, :elo)
                ON CONFLICT (player_id, surface, match_id)
                DO NOTHING
            """),
            rows
        )


if __name__ == "__main__":
    rows = build_elo_surface()
    save_to_db(rows)
    print(f"✅ Elo per superficie calcolato e salvato ({len(rows)} record)")
