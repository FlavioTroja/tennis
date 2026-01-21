from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from app.database import engine

router = APIRouter()


def ensure_value_bets_table():
    """Crea la tabella value_bets se non esiste."""
    create_sql = text("""
        CREATE TABLE IF NOT EXISTS value_bets (
            id SERIAL PRIMARY KEY,
            provider VARCHAR(50),
            bookmaker VARCHAR(50),
            model_name VARCHAR(50),
            model_version VARCHAR(50),
            min_edge_rule FLOAT,
            event_id VARCHAR(100),
            commence_time TIMESTAMP,
            player_a_id INTEGER REFERENCES players(id),
            player_a_name VARCHAR(200),
            player_b_id INTEGER REFERENCES players(id),
            player_b_name VARCHAR(200),
            side VARCHAR(1),
            prob_a FLOAT,
            prob_b FLOAT,
            odds_a FLOAT,
            odds_b FLOAT,
            edge_a FLOAT,
            edge_b FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, bookmaker, model_name)
        )
    """)
    
    with engine.begin() as conn:
        conn.execute(create_sql)


@router.get("/value-bets")
def get_value_bets():
    """Ritorna le value bets attive."""
    
    # Assicurati che la tabella esista
    try:
        ensure_value_bets_table()
    except Exception:
        pass  # Ignora errori di creazione
    
    query = text("""
        SELECT
            vb.event_id AS match_id,
            vb.commence_time,
            COALESCE(pa.name, vb.player_a_name) AS player_a,
            COALESCE(pb.name, vb.player_b_name) AS player_b,
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
        LEFT JOIN players pa ON pa.id = vb.player_a_id
        LEFT JOIN players pb ON pb.id = vb.player_b_id
        WHERE vb.edge_a >= 0.03 OR vb.edge_b >= 0.03
        ORDER BY vb.commence_time ASC
    """)

    try:
        with engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [dict(row) for row in rows]
    except ProgrammingError:
        # Tabella non esiste ancora
        return []
