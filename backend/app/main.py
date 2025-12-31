from fastapi import FastAPI
from app.database import engine
from app.models.base import Base

from app.models.player import Player
from app.models.match import Match

from app.predict import router as predict_router

app = FastAPI(title="Tennis Prediction Backend")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(predict_router)
