from sqlalchemy import Column, Integer, String, Date
from .base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    hand = Column(String(1))          # R / L / U
    height = Column(Integer)          # cm
    country = Column(String(3))       # ISO code
    birth_date = Column(Date)         # Data di nascita

    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}')>"
