from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine

router = APIRouter()


@router.get("/value-bets")
def get_value_bets():
    query = text("""
        SELECT
            vb.event_id AS match_id,
            vb.commence_time,
            pa.name AS player_a,
            pb.name AS player_b,
            vb.prob_a,
            vb.prob_b,
            vb.odds_a,
            vb.odds_b,
            vb.edge_a,
            vb.edge_b,
            CASE
                WHEN vb.edge_a > vb.edge_b THEN 'A'
                ELSE 'B'
            END AS bet_side
        FROM value_bets vb
        JOIN players pa ON pa.id = vb.player_a_id
        JOIN players pb ON pb.id = vb.player_b_id
        WHERE vb.edge_a >= 0.03 OR vb.edge_b >= 0.03
        ORDER BY vb.commence_time ASC
    """)

    with engine.begin() as conn:
        rows = conn.execute(query).mappings().all()

    return rows
