import glob
import os
from datetime import datetime

import pandas as pd
from tqdm import tqdm
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.player import Player
from app.models.match import Match

DATA_DIR = "/data/raw"

def clean_int(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    return int(value)

def parse_date(value):
    if pd.isna(value):
        return None
    return datetime.strptime(str(value), "%Y%m%d").date()


def get_or_create_player(db: Session, name, hand, height, country):
    player = db.query(Player).filter_by(name=name).first()
    if player:
        return player

    player = Player(
        name=name,
        hand=hand,
        height=clean_int(height),
        country=country,
    )
    db.add(player)
    db.flush()  # ottiene ID senza commit
    return player


def import_csv_file(csv_path: str, db: Session):
    df = pd.read_csv(csv_path)
    df = df.where(pd.notna(df), None)

    for _, row in tqdm(df.iterrows(), total=len(df), desc=os.path.basename(csv_path)):
        winner = get_or_create_player(
            db,
            name=row["winner_name"],
            hand=row["winner_hand"],
            height=row["winner_ht"],
            country=row["winner_ioc"],
        )

        loser = get_or_create_player(
            db,
            name=row["loser_name"],
            hand=row["loser_hand"],
            height=row["loser_ht"],
            country=row["loser_ioc"],
        )

        match = Match(
            match_date=parse_date(row["tourney_date"]),
            surface=row["surface"],
            tournament_name=row["tourney_name"],
            tournament_level=row["tourney_level"],
            round=row["round"],
            best_of=clean_int(row["best_of"]),
            winner_id=winner.id,
            loser_id=loser.id,
            winner_rank=clean_int(row["winner_rank"]),
            loser_rank=clean_int(row["loser_rank"]),
            score=row["score"],
        )

        db.add(match)

    db.commit()


def main():
    db = SessionLocal()

    csv_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "atp_matches_[0-9][0-9][0-9][0-9].csv"))
    )

    if not csv_files:
        print("❌ Nessun CSV trovato in data/raw/")
        return

    for csv_file in csv_files:
        print(f"\n📥 Importo {csv_file}")
        import_csv_file(csv_file, db)

    db.close()
    print("\n✅ Import completato con successo")


if __name__ == "__main__":
    main()
