import json
import time
from datetime import datetime, timedelta

import requests as req
from app.models import Feedback, Result, Session, System, db
from flask import current_app
from pytz import timezone
from app.extensions import scheduler


def update_expired_sessions(sessions_not_exited):
    for session in sessions_not_exited:
        tz = timezone("Europe/Berlin")
        delta = datetime.now(tz).replace(tzinfo=None) - session.start
        if delta.seconds > current_app.config["SESSION_EXPIRATION"]:
            complete = True
            feedbacks = Feedback.query.filter_by(session_id=session.id).all()
            if len(feedbacks) == 0:
                complete = False
            for feedback in feedbacks:
                results = Result.query.filter_by(feedback_id=feedback.id).all()
                if len(results) == 0:
                    complete = False

            if complete:
                session.exit = True
                db.session.add(session)
                db.session.commit()
            else:
                if (
                    delta.seconds > 60 * 60 * 24 * 3
                ):  # session longer than three days will be deleted TODO: add to yml-file
                    # 1. get all results that are NOT interleaved results
                    results_not_tdi = Result.query.filter(
                        Result.id != Result.tdi, Result.session_id == session.id
                    ).all()
                    for result in results_not_tdi:
                        db.session.delete(result)
                        db.session.commit()
                    # 2. get all remaining results that ARE interleaved results
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


def update_token():
    r = req.post(
        current_app.config["STELLA_SERVER_API"] + "/tokens",
        auth=(
            current_app.config["STELLA_SERVER_USER"],
            current_app.config["STELLA_SERVER_PASS"],
        ),
    )
    print(r)
    r_json = json.loads(r.text)
    print(r_json)
    delta_exp = r_json.get("expiration")
    # get new token five min (300 s) before expiration
    current_app.config["TOKEN_EXPIRATION"] = datetime.now() + timedelta(
        seconds=delta_exp - 300
    )
    current_app.config["STELLA_SERVER_TOKEN"] = r_json.get("token")


def get_side_identifier():
    r = req.get(
        current_app.config["STELLA_SERVER_API"]
        + "/sites/"
        + current_app.config["STELLA_SERVER_USERNAME"],
        auth=(current_app.config["STELLA_SERVER_TOKEN"], ""),
    )
    r_json = json.loads(r.text)

    return r_json.get("id")


def post_session(session, site_id):

    system_ranking = System.query.filter_by(
        id=session.system_ranking, type="RANK"
    ).first()
    system_recommendation = System.query.filter_by(
        id=session.system_recommendation, type="REC"
    ).first()
    system_ranking_name = system_ranking.name if system_ranking else None
    system_recommendation_name = (
        system_recommendation.name if system_recommendation else None
    )

    payload = {
        "site_user": session.site_user,
        "start": session.start.strftime("%Y-%m-%d %H:%M:%S"),
        "end": (
            session.start + timedelta(0, current_app.config["SESSION_EXPIRATION"])
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "system_ranking": system_ranking_name,
        "system_recommendation": system_recommendation_name,
    }

    r = req.post(
        current_app.config["STELLA_SERVER_API"]
        + "/sites/"
        + str(site_id)
        + "/sessions",
        data=payload,
        auth=(current_app.config["STELLA_SERVER_TOKEN"], ""),
    )
    r_json = json.loads(r.text)

    return r_json["session_id"]


def post_feedback(feedback, session_id_server):
    payload = {
        "start": feedback.start.strftime("%Y-%m-%d %H:%M:%S"),
        "end": feedback.start.strftime("%Y-%m-%d %H:%M:%S"),  # add end datetime
        "interleave": feedback.interleave,
        "clicks": (
            feedback.clicks
            if type(feedback.clicks) is str
            else json.dumps(feedback.clicks)
        ),
    }
    # post feedback from local db
    r = req.post(
        current_app.config["STELLA_SERVER_API"]
        + "/sessions/"
        + str(session_id_server)
        + "/feedbacks",
        data=payload,
        auth=(current_app.config["STELLA_SERVER_TOKEN"], ""),
    )

    # get feedback id from stella-server
    r_json = json.loads(r.text)

    return r_json["feedback_id"]


def post_result(result, feedback_id_server):
    system = System.query.filter_by(id=result.system_id).first()
    system_name = system.name
    r = req.get(
        current_app.config["STELLA_SERVER_API"] + "/system/id/" + system_name,
        auth=(current_app.config["STELLA_SERVER_TOKEN"], ""),
    )
    r_dict = json.loads(r.text)
    system_id_server = r_dict.get("system_id")

    payload = {
        "q": result.q,
        "q_date": result.q_date,
        "q_time": result.q_time,
        "system_id": system_id_server,
        "num_found": result.num_found,
        "page": result.page,
        "rpp": result.rpp,
        "items": json.dumps(result.items),
    }

    # post rankings to stella-server with (remote) feedback id
    if result.type == "RANK":
        r = req.post(
            current_app.config["STELLA_SERVER_API"]
            + "/feedbacks/"
            + str(feedback_id_server)
            + "/rankings",
            data=payload,
            auth=(current_app.config["STELLA_SERVER_TOKEN"], ""),
        )
    else:
        r = req.post(
            current_app.config["STELLA_SERVER_API"]
            + "/feedbacks/"
            + str(feedback_id_server)
            + "/recommendations",
            data=payload,
            auth=(current_app.config["STELLA_SERVER_TOKEN"], ""),
        )

    return r.status_code


def delete_exited_session(session):
    # 1. get all results that are NOT interleaved results
    results_not_tdi = Result.query.filter(
        Result.id != Result.tdi, Result.session_id == session.id
    ).all()
    for result in results_not_tdi:
        db.session.delete(result)
        db.session.commit()
    # 2. get all remaining results that ARE interleaved results
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
    if current_app.config["DEBUG"]:
        print("Session with " + str(len(feedbacks)) + " feedbacks")

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
        if current_app.config["DELETE_SENT_SESSION"]:
            delete_exited_session(session)


def check_db_sessions():
    with scheduler.app.app_context():
        scheduler.app.logger.info("Scheduler enters task.")

        sessions_not_exited = Session.query.filter_by(exit=False, sent=False).all()

        scheduler.app.logger.info(
            "There is/are " + str(len(sessions_not_exited)) + " running session(s)."
        )

        # set expired sessions to 'exit'
        update_expired_sessions(sessions_not_exited)

        sessions_exited = Session.query.filter_by(exit=True, sent=False).all()

        if (
            current_app.config["STELLA_SERVER_TOKEN"] is None
            or current_app.config["TOKEN_EXPIRATION"] < datetime.now()
        ):
            update_token()

        if len(sessions_exited) > 0:
            post_sessions(sessions_exited)
