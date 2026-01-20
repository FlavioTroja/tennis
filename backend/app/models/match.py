from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Float,
    ForeignKey
)
from sqlalchemy.orm import relationship
from .base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)

    # Info torneo
    match_date = Column(Date, nullable=False, index=True)
    surface = Column(String)
    tournament_name = Column(String)
    tournament_level = Column(String(1))  # G=Grand Slam, M=Masters, A=ATP500, etc.
    round = Column(String)
    best_of = Column(Integer)
    minutes = Column(Integer)  # Durata match

    # Giocatori
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    loser_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Ranking e seed
    winner_rank = Column(Integer)
    loser_rank = Column(Integer)
    winner_seed = Column(Integer)
    loser_seed = Column(Integer)

    # Età al momento del match
    winner_age = Column(Float)
    loser_age = Column(Float)

    # Punteggio
    score = Column(String)

    # Statistiche servizio winner
    w_ace = Column(Integer)
    w_df = Column(Integer)      # Double faults
    w_svpt = Column(Integer)    # Serve points
    w_1stIn = Column(Integer)   # First serves in
    w_1stWon = Column(Integer)  # First serve points won
    w_2ndWon = Column(Integer)  # Second serve points won
    w_SvGms = Column(Integer)   # Service games
    w_bpSaved = Column(Integer) # Break points saved
    w_bpFaced = Column(Integer) # Break points faced

    # Statistiche servizio loser
    l_ace = Column(Integer)
    l_df = Column(Integer)
    l_svpt = Column(Integer)
    l_1stIn = Column(Integer)
    l_1stWon = Column(Integer)
    l_2ndWon = Column(Integer)
    l_SvGms = Column(Integer)
    l_bpSaved = Column(Integer)
    l_bpFaced = Column(Integer)

    # Relationships
    winner = relationship("Player", foreign_keys=[winner_id])
    loser = relationship("Player", foreign_keys=[loser_id])

    def __repr__(self):
        return f"<Match(id={self.id}, date={self.match_date})>"
