from fastapi import FastAPI
from app.database import engine
from app.models.base import Base

from app.models.player import Player
from app.models.match import Match

app = FastAPI(title="Tennis Prediction Backend")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}
