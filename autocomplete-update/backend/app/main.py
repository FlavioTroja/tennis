import logging
from fastapi import FastAPI

from app.database import engine
from app.models.base import Base
from app.models.player import Player
from app.models.match import Match

from app.services.scheduler import start_scheduler
from app.routes.predict import router as predict_router
from app.routes.value_bets import router as value_bets_router
from app.routes.players import router as players_router

# --------------------------------------------------
# LOGGING CONFIG (globale)
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("tennis-backend")

# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------
app = FastAPI(title="Tennis Prediction Backend")

# --------------------------------------------------
# STARTUP EVENTS
# --------------------------------------------------
@app.on_event("startup")
def startup_db():
    logger.info("Initializing database schema")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready")

@app.on_event("startup")
def startup_scheduler():
    logger.info("Starting scheduler")
    start_scheduler()
    logger.info("Scheduler started")

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.get("/health")
def health():
    logger.debug("Healthcheck called")
    return {"status": "ok"}

app.include_router(predict_router)
app.include_router(value_bets_router)
app.include_router(players_router)

logger.info("Application routes loaded")
