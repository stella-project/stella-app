import logging
import time
import json
from config import conf
from .models import db, Session, Result, Feedback, System
from apscheduler.schedulers.background import BackgroundScheduler
import requests as req
from datetime import datetime, timedelta

API = conf['app']['STELLA_SERVER_API']
USER = conf['app']['STELLA_SERVER_USER']
PASS = conf['app']['STELLA_SERVER_PASS']
USERNAME = conf['app']['STELLA_SERVER_USERNAME']


def update_expired_sessions(sessions_not_exited):
    for session in sessions_not_exited:
        delta = datetime.now() - session.start
        if delta.seconds > conf['app']['SESSION_EXPIRATION']:
            session.exit = True
            db.session.add(session)
            db.session.commit()


def update_token():
    r = req.post(API + '/tokens', auth=(USER, PASS))
    r_json = json.loads(r.text)
    delta_exp = r_json.get('expiration')
    # get new token five min (300 s) before expiration
    conf['app']['TOKEN_EXPIRATION'] = datetime.now() + timedelta(seconds=delta_exp - 300)
    conf["app"]["STELLA_SERVER_TOKEN"] = r_json.get('token')


def get_side_identifier():
    r = req.get(API + '/sites/' + USERNAME, auth=(conf["app"].get("STELLA_SERVER_TOKEN"), ''))
    r_json = json.loads(r.text)

    return r_json.get('id')


def post_session(session, site_id):
    payload = {
        'site_user': session.site_user,
        'start': session.start.strftime("%Y-%m-%d %H:%M:%S"),
        'end': session.start.strftime("%Y-%m-%d %H:%M:%S"),
        'system_ranking': System.query.filter_by(id=session.system_ranking, type='RANK').first().name,
        'system_recommendation': System.query.filter_by(id=session.system_recommendation, type='REC').first().name
    }

    r = req.post(API + '/sites/' + str(site_id) + '/sessions',
                 data=payload,
                 auth=(conf["app"].get("STELLA_SERVER_TOKEN"), ''))
    r_json = json.loads(r.text)

    return r_json['session_id']


def post_feedback(feedback, session_id_server):
    payload = {
        'start': feedback.start.strftime("%Y-%m-%d %H:%M:%S"),
        'end': feedback.start.strftime("%Y-%m-%d %H:%M:%S"),  # add end datetime
        'interleave': feedback.interleave,
        'clicks': (feedback.clicks if type(feedback.clicks) is str else json.dumps(feedback.clicks))
    }
    # post feedback from local db
    r = req.post(API + '/sessions/' + str(session_id_server) + '/feedbacks',
                 data=payload,
                 auth=(conf["app"].get("STELLA_SERVER_TOKEN"), ''))

    # get feedback id from stella-server
    r_json = json.loads(r.text)

    return r_json['feedback_id']


def post_result(result, feedback_id_server):
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
                 auth=(conf["app"].get("STELLA_SERVER_TOKEN"), ''))

    return r.status_code


def delete_exited_session(session):
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


def post_results(results, feedback_id_server):
    for result in results:
        # POST result
        post_result(result, feedback_id_server)


def post_feedbacks(session, session_id_server):
    feedbacks = Feedback.query.filter_by(session_id=session.id).all()
    if conf['app']['DEBUG']:
        print('Session with ' + str(len(feedbacks)) + " feedbacks")

    for feedback in feedbacks:
        # POST feedback
        feedback_id_server = post_feedback(feedback, session_id_server)

        # post results
        results = Result.query.filter_by(feedback_id=feedback.id).all()
        post_results(results, feedback_id_server)


def post_sessions(sessions_exited):
    for session in sessions_exited:

        # get site identifier
        site_id = get_side_identifier()

        # POST session/make new session
        session_id_server = post_session(session, site_id)

        # post feedbacks
        post_feedbacks(session, session_id_server)

        # set status to sent=True
        session.sent = True
        db.session.add(session)
        db.session.commit()

        # optionally delete entry from local database
        if conf['app']['DELETE_SENT_SESSION']:
            delete_exited_session(session)


def check_db_sessions(app_context):
    with app_context:
        logger = logging.getLogger("stella-app")
        sessions_not_exited = Session.query.filter_by(exit=False, sent=False).all()
        logger.info(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))
        logger.info('There is/are ' + str(len(sessions_not_exited)) + ' running session(s).')
        if conf['app']['DEBUG']:
            print('There is/are ' + str(len(sessions_not_exited)) + ' running session(s).')

        # set expired sessions to 'exit'
        update_expired_sessions(sessions_not_exited)

        sessions_exited = Session.query.filter_by(exit=True, sent=False).all()
        if conf['app']['DEBUG']:
            print('There is/are ' + str(len(sessions_exited)) + ' exited session(s).')

        if conf["app"].get("STELLA_SERVER_TOKEN") is None or conf['app']['TOKEN_EXPIRATION'] < datetime.now():
            update_token()

        if len(sessions_exited) > 0:
            post_sessions(sessions_exited)


def cron(app_context):
    conf['app']['TOKEN_EXPIRATION'] = datetime.now()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: check_db_sessions(app_context),
                      trigger="interval",
                      seconds=conf['app']['INTERVAL_DB_CHECK'])
    return scheduler
