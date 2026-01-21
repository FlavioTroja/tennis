"""
Players API Routes
==================
Endpoint per ricerca e info giocatori.
"""

from fastapi import APIRouter, Query
from sqlalchemy import text
from typing import Optional
from app.database import engine

router = APIRouter(tags=["players"])


@router.get("/players/search")
def search_players(
    q: str = Query(..., min_length=2, description="Query di ricerca (min 2 caratteri)"),
    limit: int = Query(10, ge=1, le=50, description="Numero massimo risultati"),
):
    """
    Cerca giocatori per nome (case-insensitive, match parziale).
    
    Esempi:
    - /players/search?q=djok -> Novak Djokovic
    - /players/search?q=nad -> Rafael Nadal
    - /players/search?q=alcaraz -> Carlos Alcaraz
    """
    
    # Cerca match parziale, ordinato per rilevanza
    query = text("""
        SELECT 
            p.id,
            p.name,
            p.country,
            p.hand,
            -- Conta match recenti per ordinare per "attività"
            (
                SELECT COUNT(*) 
                FROM matches m 
                WHERE (m.winner_id = p.id OR m.loser_id = p.id)
                AND m.match_date > CURRENT_DATE - INTERVAL '2 years'
            ) as recent_matches
        FROM players p
        WHERE p.name ILIKE :pattern
        ORDER BY 
            -- Prima i match esatti all'inizio del nome
            CASE WHEN p.name ILIKE :start_pattern THEN 0 ELSE 1 END,
            -- Poi per attività recente
            recent_matches DESC,
            -- Infine alfabetico
            p.name ASC
        LIMIT :limit
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(query, {
            "pattern": f"%{q}%",
            "start_pattern": f"{q}%",
            "limit": limit
        }).mappings().all()
    
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "country": row["country"],
            "hand": row["hand"],
            "recent_matches": row["recent_matches"],
        }
        for row in rows
    ]


@router.get("/players/{player_id}")
def get_player(player_id: int):
    """Ritorna i dettagli di un giocatore."""
    
    query = text("""
        SELECT 
            p.id,
            p.name,
            p.country,
            p.hand,
            p.height,
            p.birth_date,
            -- Stats aggregate
            (SELECT COUNT(*) FROM matches WHERE winner_id = p.id) as total_wins,
            (SELECT COUNT(*) FROM matches WHERE loser_id = p.id) as total_losses,
            -- Ultimo match
            (
                SELECT MAX(match_date) 
                FROM matches 
                WHERE winner_id = p.id OR loser_id = p.id
            ) as last_match,
            -- Elo per superficie
            (SELECT elo FROM player_surface_state WHERE player_id = p.id AND surface = 'Hard') as elo_hard,
            (SELECT elo FROM player_surface_state WHERE player_id = p.id AND surface = 'Clay') as elo_clay,
            (SELECT elo FROM player_surface_state WHERE player_id = p.id AND surface = 'Grass') as elo_grass
        FROM players p
        WHERE p.id = :player_id
    """)
    
    with engine.connect() as conn:
        row = conn.execute(query, {"player_id": player_id}).mappings().first()
    
    if not row:
        return {"error": "Player not found"}, 404
    
    return dict(row)


@router.get("/players/top")
def get_top_players(
    limit: int = Query(20, ge=1, le=100),
    surface: Optional[str] = Query(None, regex="^(Hard|Clay|Grass)$"),
):
    """Ritorna i top giocatori per Elo (opzionalmente per superficie)."""
    
    if surface:
        query = text("""
            SELECT 
                p.id,
                p.name,
                p.country,
                pss.elo,
                pss.matches_cnt,
                pss.wins_cnt
            FROM players p
            JOIN player_surface_state pss ON pss.player_id = p.id
            WHERE pss.surface = :surface
            AND pss.matches_cnt >= 10
            ORDER BY pss.elo DESC
            LIMIT :limit
        """)
        params = {"surface": surface, "limit": limit}
    else:
        # Media Elo su tutte le superfici
        query = text("""
            SELECT 
                p.id,
                p.name,
                p.country,
                AVG(pss.elo) as elo,
                SUM(pss.matches_cnt) as matches_cnt,
                SUM(pss.wins_cnt) as wins_cnt
            FROM players p
            JOIN player_surface_state pss ON pss.player_id = p.id
            GROUP BY p.id, p.name, p.country
            HAVING SUM(pss.matches_cnt) >= 10
            ORDER BY AVG(pss.elo) DESC
            LIMIT :limit
        """)
        params = {"limit": limit}
    
    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().all()
    
    return [dict(row) for row in rows]
