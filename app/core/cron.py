import time
import logging
from core.models import db, Session

from apscheduler.schedulers.background import BackgroundScheduler

def print_date_time():
    sessions = Session.query.filter_by(exit=True, sent=False)

    logger = logging.getLogger("stella-app")
    logger.info(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


def scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=print_date_time, trigger="interval", seconds=3)
    return scheduler
