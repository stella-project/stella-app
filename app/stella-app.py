import logging
import time
from core import create_app
from core.models import System, Session, Result, Feedback
from apscheduler.schedulers.background import BackgroundScheduler

app = create_app('default')


def print_date_time():
    with app.app_context():
        sessions_exited = Session.query.filter_by(exit=True, sent=False).all()
        num_sessions = len(sessions_exited)
        if num_sessions > 0:
            logger = logging.getLogger("stella-app")
            logger.info(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
            logger.info('There is/are ' + str(num_sessions) + ' exited session(s).')
            print('There is/are ' + str(num_sessions) + ' exited session(s).')

            for session in sessions_exited:
                # get all results (rankings/recommendations) assigned with sesssion
                rankings = Result.query.filter_by(session_id=session.id).all()
                print('Session with ' + str(len(rankings)) + " rankings")

                # get all feedbacks assigned with session
                feedbacks = Result.query.filter_by(session_id=session.id).all()
                print('Session with ' + str(len(feedbacks)) + " feedbacks")

                # upload them to the stella-server

                # set status to sent=True

                # optionally delete entry from localdatabase

        sessions_not_exited = Session.query.filter_by(exit=False, sent=False).all()
        num_sessions = len(sessions_not_exited)
        print('There is/are ' + str(num_sessions) + ' running session(s).')


def scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=print_date_time, trigger="interval", seconds=3)
    return scheduler


if __name__ == '__main__':
    cron = scheduler()
    cron.start()
    logger = logging.getLogger("stella-app")
    logger.info("Starting app...")
    app.run(host='0.0.0.0', port=8000, debug=False)

