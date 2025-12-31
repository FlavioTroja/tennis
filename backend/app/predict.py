from datetime import date
import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import engine
from sqlalchemy import text

router = APIRouter()

MODEL_PATH = "/data/ml/tennis_model.joblib"
model = joblib.load(MODEL_PATH)


class PredictRequest(BaseModel):
    player_a: str
    player_b: str
    surface: str
    match_date: date


@router.post("/predict")
def predict(req: PredictRequest):
    with engine.connect() as conn:
        # recupera player_id
        players = conn.execute(
            text("SELECT id, name FROM players WHERE name IN (:a, :b)"),
            {"a": req.player_a, "b": req.player_b},
        ).fetchall()

        if len(players) != 2:
            raise HTTPException(status_code=404, detail="Giocatore non trovato")

        pid = {p.name: p.id for p in players}
        A, B = pid[req.player_a], pid[req.player_b]

        rank_rows = conn.execute(
            text("""
            SELECT
                p.id AS player_id,
                r.rank
            FROM players p
            JOIN (
                SELECT
                    winner_id AS player_id,
                    winner_rank AS rank,
                    match_date
                FROM matches
                WHERE winner_rank IS NOT NULL

                UNION ALL

                SELECT
                    loser_id AS player_id,
                    loser_rank AS rank,
                    match_date
                FROM matches
                WHERE loser_rank IS NOT NULL
            ) r ON r.player_id = p.id
            WHERE p.id IN (:a, :b)
            ORDER BY r.match_date DESC
            """),
            {"a": A, "b": B},
        ).fetchall()

        latest_rank = {}
        for row in rank_rows:
            if row.player_id not in latest_rank:
                latest_rank[row.player_id] = row.rank

        # DEBUG TEMPORANEO (IMPORTANTE)
        print("DEBUG ranking:", latest_rank)

        if A not in latest_rank or B not in latest_rank:
            raise HTTPException(
                status_code=400,
                detail=f"Ranking non disponibile (A={A in latest_rank}, B={B in latest_rank})"
            )

        rank_A = latest_rank[A]
        rank_B = latest_rank[B]

        if rank_A is None or rank_B is None:
            raise HTTPException(status_code=400, detail="Ranking non disponibile")

        # recent form + surface
        def scalar(sql, params):
            v = conn.execute(text(sql), params).scalar()
            return float(v) if v is not None else 0.0

        recent_sql = """
        SELECT AVG(win) FROM (
            SELECT win FROM player_matches
            WHERE player_id = :p AND match_date < :d
            ORDER BY match_date DESC LIMIT :n
        ) t;
        """

        surface_sql = """
        SELECT AVG(win)
        FROM player_matches
        WHERE player_id = :p AND surface = :s AND match_date < :d;
        """

        h2h_sql = """
        SELECT COUNT(*) FROM player_matches
        WHERE player_id = :a AND opponent_id = :b AND win = 1
          AND match_date < :d;
        """

        A_r5 = scalar(recent_sql, {"p": A, "d": req.match_date, "n": 5})
        B_r5 = scalar(recent_sql, {"p": B, "d": req.match_date, "n": 5})

        A_r10 = scalar(recent_sql, {"p": A, "d": req.match_date, "n": 10})
        B_r10 = scalar(recent_sql, {"p": B, "d": req.match_date, "n": 10})

        A_surf = scalar(surface_sql, {"p": A, "s": req.surface, "d": req.match_date})
        B_surf = scalar(surface_sql, {"p": B, "s": req.surface, "d": req.match_date})

        A_h2h = scalar(h2h_sql, {"a": A, "b": B, "d": req.match_date})
        B_h2h = scalar(h2h_sql, {"a": B, "b": A, "d": req.match_date})

    X = pd.DataFrame([{
        "ranking_diff": rank_A - rank_B,
        "recent_5_diff": A_r5 - B_r5,
        "recent_10_diff": A_r10 - B_r10,
        "surface_diff": A_surf - B_surf,
        "h2h_diff": A_h2h - B_h2h,
    }])

    prob_A = model.predict_proba(X)[0, 1]

    return {
        "player_a": req.player_a,
        "player_b": req.player_b,
        "player_a_win_probability": round(prob_A, 3),
        "player_b_win_probability": round(1 - prob_A, 3),
    }
