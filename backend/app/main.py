from fastapi import FastAPI
from app.database import engine
from app.models.base import Base

from app.models.player import Player
from app.models.match import Match

from app.services.scheduler import start_scheduler
from app.routes.predict import router as predict_router

app = FastAPI(title="Tennis Prediction Backend")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(predict_router)
