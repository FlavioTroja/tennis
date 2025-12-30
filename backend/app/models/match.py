from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey
)
from sqlalchemy.orm import relationship
from .base import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)

    match_date = Column(Date, nullable=False, index=True)
    surface = Column(String)
    tournament_name = Column(String)
    tournament_level = Column(String(1))
    round = Column(String)
    best_of = Column(Integer)

    winner_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    loser_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    winner_rank = Column(Integer)
    loser_rank = Column(Integer)

    score = Column(String)

    winner = relationship("Player", foreign_keys=[winner_id])
    loser = relationship("Player", foreign_keys=[loser_id])

    def __repr__(self):
        return f"<Match(id={self.id}, date={self.match_date})>"

