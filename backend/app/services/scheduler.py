from apscheduler.schedulers.background import BackgroundScheduler
from ml.run_odds_pipeline import main as odds_pipeline

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler():
    # Esegue ogni 12 ore (2 volte al giorno)
    # Con piano free The Odds API (500 crediti/mese):
    # - ~8 crediti per chiamata
    # - 2 chiamate/giorno = ~16 crediti/giorno
    # - ~480 crediti/mese = OK
    scheduler.add_job(
        odds_pipeline,
        trigger="interval",
        hours=24,
        id="odds_pipeline",
        replace_existing=True
    )
    scheduler.start()
