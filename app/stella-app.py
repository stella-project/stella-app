import logging
import time
import json
from app.config import conf
from core import create_app
from core.models import db, System, Session, Result, Feedback
from apscheduler.schedulers.background import BackgroundScheduler
import requests as req
from datetime import datetime, timedelta

app = create_app('default')


def check_db_sessions():
    with app.app_context():

        sessions_not_exited = Session.query.filter_by(exit=False, sent=False).all()
        num_sessions = len(sessions_not_exited)
        print('There is/are ' + str(num_sessions) + ' running session(s).')

        # set expired sessions to 'exit'
        for session in sessions_not_exited:
            delta = datetime.now() - session.start
            if delta.seconds > conf['app']['SESSION_EXPIRATION']:
                session.exit = True
                db.session.add(session)
                db.session.commit()

        sessions_exited = Session.query.filter_by(exit=True, sent=False).all()
        num_sessions = len(sessions_exited)
        if num_sessions > 0:
            logger = logging.getLogger("stella-app")
            logger.info(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
            logger.info('There is/are ' + str(num_sessions) + ' exited session(s).')
            print('There is/are ' + str(num_sessions) + ' exited session(s).')

            for session in sessions_exited:

                API = conf['app']['STELLA_SERVER_API']
                USER = conf['app']['STELLA_SERVER_USER']
                PASS = conf['app']['STELLA_SERVER_PASS']
                USERNAME = conf['app']['STELLA_SERVER_USERNAME']

                # get token if not available
                if conf["app"].get("STELLA_SERVER_TOKEN") is None or conf['app']['TOKEN_EXPIRATION'] < datetime.now():
                    r = req.post(API + '/tokens', auth=(USER, PASS))
                    r_json = json.loads(r.text)
                    delta_exp = r_json.get('expiration')
                    conf['app']['TOKEN_EXPIRATION'] = datetime.now() + timedelta(seconds=delta_exp - 300)  # get new token five min before expiration
                    conf["app"]["STELLA_SERVER_TOKEN"] = r_json.get('token')

                TOKEN = conf["app"]["STELLA_SERVER_TOKEN"]

                # make new session
                # get site identifier
                r = req.get(API + '/sites/' + USERNAME, auth=(TOKEN, ''))
                r_json = json.loads(r.text)
                site_id = r_json.get('id')

                payload = {
                    'site_user': session.site_user,
                    'start': session.start.strftime("%Y-%m-%d %H:%M:%S"),
                    'end': session.start.strftime("%Y-%m-%d %H:%M:%S"),
                    'system_ranking': 'Experimental Ranker A',
                    'system_recommendation': 'Experimental Recommender A'
                }

                # POST session
                r = req.post(API + '/sites/' + str(site_id) + '/sessions', data=payload, auth=(TOKEN, ''))
                r_json = json.loads(r.text)
                session_id_server = r_json['session_id']

                # get all results (rankings/recommendations) assigned with session
                rankings = Result.query.filter_by(session_id=session.id).all()
                print('Session with ' + str(len(rankings)) + " rankings")

                # get all feedbacks assigned with session
                feedbacks = Feedback.query.filter_by(session_id=session.id).all()
                print('Session with ' + str(len(feedbacks)) + " feedbacks")

                print(conf['app']['STELLA_SERVER_API'])
                for feedback in feedbacks:

                    payload = {
                        'start': feedback.start.strftime("%Y-%m-%d %H:%M:%S"),
                        'end': feedback.start.strftime("%Y-%m-%d %H:%M:%S"),  # add end datetime
                        'interleave': True,
                        'clicks': json.dumps(feedback.clicks)
                    }

                    # post feedback from local db
                    r = req.post(API + '/sessions/' + str(session_id_server) + '/feedbacks',
                                 data=payload,
                                 auth=(TOKEN, ''))

                    # get feedback id from stella-server
                    r_json = json.loads(r.text)
                    feedback_id_server = r_json['feedback_id']

                    # get all rankings for local feedback id
                    results = Result.query.filter_by(feedback_id=feedback.id).all()
                    for result in results:
                        payload = {
                            'q': result.q,
                            'q_date': result.q_date,
                            'q_time': result.q_time,
                            'num_found': result.num_found,
                            'page': result.page,
                            'rpp': result.rpp,
                            'items': json.dumps(result.items)
                        }

                        # post rankings to stella-server with (remote) feedback id
                        r = req.post(API + '/feedbacks/' + str(feedback_id_server) + '/rankings',
                                     data=payload,
                                     auth=(TOKEN, ''))
                        print(r.text)

                # set status to sent=True
                session.sent = True
                db.session.add(session)
                db.session.commit()

                # optionally delete entry from local database
                if conf['app']['DELETE_SENT_SESSION']:
                    results = Result.query.filter_by(session_id=session.id).all()
                    for result in results:
                        db.session.delete(result)
                        db.session.commit()
                    feedbacks = Feedback.query.filter_by(session_id=session.id).all()
                    for feedback in feedbacks:
                        db.session.delete(feedback)
                        db.session.commit()
                    db.session.delete(session)
                    db.session.commit()


def scheduler():
    conf['app']['TOKEN_EXPIRATION'] = datetime.now()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_db_sessions, trigger="interval", seconds=conf['app']['INTERVAL_DB_CHECK'])
    return scheduler


if __name__ == '__main__':
    cron = scheduler()
    cron.start()
    logger = logging.getLogger("stella-app")
    logger.info("Starting app...")
    app.run(host='0.0.0.0', port=8000, debug=False)
