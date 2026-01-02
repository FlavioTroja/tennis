from apscheduler.schedulers.background import BackgroundScheduler
from ml.run_odds_pipeline import main as odds_pipeline

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler():
    scheduler.add_job(
        odds_pipeline,
        trigger="interval",
        minutes=30,
        id="edge_pipeline",
        replace_existing=True
    )
    scheduler.start()
