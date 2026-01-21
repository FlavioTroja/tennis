"""
Debug Feature Store
====================
Script per verificare lo stato delle tabelle del feature store.
Eseguire con: python -m ml.debug_feature_store
"""

from sqlalchemy import text
from app.database import engine


def check_table_exists(table_name: str) -> bool:
    """Verifica se una tabella esiste."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = :table_name
            )
        """), {"table_name": table_name}).scalar()
    return result


def count_rows(table_name: str) -> int:
    """Conta le righe in una tabella."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        return result
    except Exception as e:
        return -1


def check_player(player_name: str):
    """Verifica i dati di un giocatore specifico."""
    print(f"\n🔍 Checking player: {player_name}")
    
    with engine.connect() as conn:
        # ID giocatore
        pid = conn.execute(
            text("SELECT id FROM players WHERE name = :n"),
            {"n": player_name}
        ).scalar()
        
        if not pid:
            print(f"   ❌ Player not found!")
            return
        
        print(f"   ID: {pid}")
        
        # Player info
        player = conn.execute(
            text("SELECT name, country, hand, birth_date FROM players WHERE id = :id"),
            {"id": pid}
        ).fetchone()
        print(f"   Country: {player.country}, Hand: {player.hand}, Birth: {player.birth_date}")
        
        # Surface state
        surfaces = conn.execute(
            text("SELECT surface, elo, matches_cnt, wins_cnt FROM player_surface_state WHERE player_id = :pid"),
            {"pid": pid}
        ).fetchall()
        
        if surfaces:
            print("   📊 Surface State:")
            for s in surfaces:
                wr = s.wins_cnt / s.matches_cnt if s.matches_cnt > 0 else 0
                print(f"      {s.surface}: Elo={s.elo:.1f}, Matches={s.matches_cnt}, WR={wr:.1%}")
        else:
            print("   ⚠️ No surface state data!")
        
        # Form state
        form = conn.execute(
            text("SELECT last_results FROM player_form_state WHERE player_id = :pid"),
            {"pid": pid}
        ).fetchone()
        
        if form and form.last_results:
            results = list(form.last_results)
            print(f"   📈 Form: {len(results)} results, Last 5: {results[-5:]}")
        else:
            print("   ⚠️ No form data!")
        
        # Serve state
        serve = conn.execute(
            text("""
                SELECT svpt_total, ace_total, df_total, first_in_total, first_won_total
                FROM player_serve_state WHERE player_id = :pid
            """),
            {"pid": pid}
        ).fetchone()
        
        if serve and serve.svpt_total:
            print(f"   🎾 Serve: {serve.svpt_total} points, Ace={serve.ace_total}, DF={serve.df_total}")
        else:
            print("   ⚠️ No serve data!")
        
        # Activity state
        activity = conn.execute(
            text("SELECT last_match_date FROM player_activity_state WHERE player_id = :pid"),
            {"pid": pid}
        ).fetchone()
        
        if activity:
            print(f"   📅 Last match: {activity.last_match_date}")
        else:
            print("   ⚠️ No activity data!")
        
        # Match count
        match_count = conn.execute(
            text("""
                SELECT COUNT(*) FROM matches 
                WHERE winner_id = :pid OR loser_id = :pid
            """),
            {"pid": pid}
        ).scalar()
        print(f"   🎯 Total matches in DB: {match_count}")


def main():
    print("=" * 60)
    print("🔍 TENNIS FEATURE STORE DEBUG")
    print("=" * 60)
    
    # Check tables
    tables = [
        "players",
        "matches",
        "player_surface_state",
        "player_form_state",
        "player_serve_state",
        "player_activity_state",
        "player_level_state",
        "h2h_state",
        "player_match_features",
    ]
    
    print("\n📊 Table Status:")
    print("-" * 40)
    
    for table in tables:
        exists = check_table_exists(table)
        if exists:
            count = count_rows(table)
            status = f"✅ {count:,} rows" if count >= 0 else "❌ Error"
        else:
            status = "❌ Not exists"
        print(f"   {table:30s} {status}")
    
    # Check specific players
    test_players = ["Novak Djokovic", "Carlos Alcaraz", "Rafael Nadal", "Jannik Sinner"]
    
    for player in test_players:
        check_player(player)
    
    print("\n" + "=" * 60)
    print("📝 DIAGNOSIS:")
    print("=" * 60)
    
    # Check if feature store tables are empty
    surface_count = count_rows("player_surface_state")
    form_count = count_rows("player_form_state")
    
    if surface_count == 0 or form_count == 0:
        print("""
❌ PROBLEMA: Le tabelle del feature store sono vuote!

   Il feature store non è stato costruito. Esegui:
   
   1. docker compose exec tennis-be python -m ml.feature_store_build
   
   Questo popolerà tutte le tabelle di stato a partire dai match importati.
""")
    else:
        print(f"""
✅ Feature store sembra popolato:
   - player_surface_state: {surface_count} rows
   - player_form_state: {form_count} rows
   
   Se i dati sono ancora 0, verifica che:
   1. Il giocatore sia presente nel database
   2. Il giocatore abbia match importati
""")


if __name__ == "__main__":
    main()
