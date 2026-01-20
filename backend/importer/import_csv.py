"""
Tennis Data Importer
=====================
Importa i CSV di Jeff Sackmann (tennis_atp) nel database.
Cattura tutti i campi disponibili: dati biografici, età, statistiche servizio.
"""

import glob
import os
from datetime import datetime, date

import pandas as pd
from tqdm import tqdm
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.player import Player
from app.models.match import Match

DATA_DIR = "/data/raw"


def clean_int(value):
    """Converte in int, gestendo NaN e None."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def clean_float(value):
    """Converte in float, gestendo NaN e None."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_date(value):
    """Parsa data nel formato YYYYMMDD."""
    if pd.isna(value):
        return None
    try:
        return datetime.strptime(str(int(value)), "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def parse_birth_date(value):
    """Parsa data di nascita nel formato YYYYMMDD."""
    if pd.isna(value):
        return None
    try:
        val_str = str(int(value))
        if len(val_str) == 8:
            return datetime.strptime(val_str, "%Y%m%d").date()
        elif len(val_str) == 4:
            # Solo anno
            return date(int(val_str), 1, 1)
    except (ValueError, TypeError):
        pass
    return None


def get_or_create_player(db: Session, name, hand, height, country, birth_date=None):
    """Ottiene o crea un giocatore."""
    player = db.query(Player).filter_by(name=name).first()
    
    if player:
        # Aggiorna birth_date se mancante
        if birth_date and not player.birth_date:
            player.birth_date = birth_date
        return player

    player = Player(
        name=name,
        hand=hand,
        height=clean_int(height),
        country=country,
        birth_date=birth_date,
    )
    db.add(player)
    db.flush()
    return player


def import_csv_file(csv_path: str, db: Session):
    """Importa un singolo file CSV."""
    
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.where(pd.notna(df), None)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=os.path.basename(csv_path)):
        # Parsing date di nascita se disponibili
        winner_dob = parse_birth_date(row.get("winner_dob"))
        loser_dob = parse_birth_date(row.get("loser_dob"))
        
        # Crea/ottieni giocatori
        winner = get_or_create_player(
            db,
            name=row["winner_name"],
            hand=row.get("winner_hand"),
            height=row.get("winner_ht"),
            country=row.get("winner_ioc"),
            birth_date=winner_dob,
        )

        loser = get_or_create_player(
            db,
            name=row["loser_name"],
            hand=row.get("loser_hand"),
            height=row.get("loser_ht"),
            country=row.get("loser_ioc"),
            birth_date=loser_dob,
        )

        # Crea match
        match = Match(
            match_date=parse_date(row["tourney_date"]),
            surface=row.get("surface"),
            tournament_name=row.get("tourney_name"),
            tournament_level=row.get("tourney_level"),
            round=row.get("round"),
            best_of=clean_int(row.get("best_of")),
            minutes=clean_int(row.get("minutes")),
            
            winner_id=winner.id,
            loser_id=loser.id,
            
            winner_rank=clean_int(row.get("winner_rank")),
            loser_rank=clean_int(row.get("loser_rank")),
            winner_seed=clean_int(row.get("winner_seed")),
            loser_seed=clean_int(row.get("loser_seed")),
            
            winner_age=clean_float(row.get("winner_age")),
            loser_age=clean_float(row.get("loser_age")),
            
            score=row.get("score"),
            
            # Statistiche winner
            w_ace=clean_int(row.get("w_ace")),
            w_df=clean_int(row.get("w_df")),
            w_svpt=clean_int(row.get("w_svpt")),
            w_1stIn=clean_int(row.get("w_1stIn")),
            w_1stWon=clean_int(row.get("w_1stWon")),
            w_2ndWon=clean_int(row.get("w_2ndWon")),
            w_SvGms=clean_int(row.get("w_SvGms")),
            w_bpSaved=clean_int(row.get("w_bpSaved")),
            w_bpFaced=clean_int(row.get("w_bpFaced")),
            
            # Statistiche loser
            l_ace=clean_int(row.get("l_ace")),
            l_df=clean_int(row.get("l_df")),
            l_svpt=clean_int(row.get("l_svpt")),
            l_1stIn=clean_int(row.get("l_1stIn")),
            l_1stWon=clean_int(row.get("l_1stWon")),
            l_2ndWon=clean_int(row.get("l_2ndWon")),
            l_SvGms=clean_int(row.get("l_SvGms")),
            l_bpSaved=clean_int(row.get("l_bpSaved")),
            l_bpFaced=clean_int(row.get("l_bpFaced")),
        )

        db.add(match)

    db.commit()


def import_players_csv(csv_path: str, db: Session):
    """
    Importa il file atp_players.csv per aggiornare le date di nascita.
    Questo file ha: player_id, name_first, name_last, hand, dob, ioc
    """
    if not os.path.exists(csv_path):
        print(f"⚠️  File {csv_path} non trovato, skip")
        return
    
    print(f"\n📥 Importo dati giocatori da {csv_path}")
    
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.where(pd.notna(df), None)
    
    updated = 0
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Players"):
        name_first = row.get("name_first", "")
        name_last = row.get("name_last", "")
        
        if not name_first or not name_last:
            continue
            
        full_name = f"{name_first} {name_last}"
        birth_date = parse_birth_date(row.get("dob"))
        
        if not birth_date:
            continue
        
        # Cerca giocatore esistente
        player = db.query(Player).filter_by(name=full_name).first()
        
        if player and not player.birth_date:
            player.birth_date = birth_date
            updated += 1
    
    db.commit()
    print(f"   Aggiornati {updated} giocatori con data di nascita")


def main():
    """Entry point principale."""
    
    print("=" * 60)
    print("🎾 TENNIS DATA IMPORTER")
    print("=" * 60)
    
    db = SessionLocal()

    # Importa match
    csv_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "atp_matches_[0-9][0-9][0-9][0-9].csv"))
    )

    if not csv_files:
        print(f"❌ Nessun CSV trovato in {DATA_DIR}/")
        print("   Scarica i file da: https://github.com/JeffSackmann/tennis_atp")
        return

    print(f"\n📂 Trovati {len(csv_files)} file CSV")
    
    for csv_file in csv_files:
        print(f"\n📥 Importo {csv_file}")
        import_csv_file(csv_file, db)

    # Importa dati giocatori per date di nascita mancanti
    players_csv = os.path.join(DATA_DIR, "atp_players.csv")
    import_players_csv(players_csv, db)

    db.close()
    
    print("\n" + "=" * 60)
    print("✅ Import completato con successo")
    print("=" * 60)


if __name__ == "__main__":
    main()
