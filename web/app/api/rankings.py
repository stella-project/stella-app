import asyncio
from datetime import datetime

from app.models import Feedback, Result, Session, System, db
from app.services.profile_service import profile_route
from app.services.result_service import get_cached_response, make_results
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import Response, current_app, json, jsonify, request
from pytz import timezone

from . import api

tz = timezone("Europe/Berlin")


@api.route("/ranking/<int:id>/feedback", methods=["POST"])
def post_feedback(id):
    """Add user feedback to database (collect data for statistics)
    Tested: True

    @param id:  ranking id (int)
    @return:    HTTP status message
    """
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

    if clicks is not None:
        ranking = db.session.query(Result).get_or_404(id)

        feedback = Feedback(
            start=ranking.q_date,
            session_id=ranking.session_id,
            interleave=ranking.tdi is not None,
            clicks=clicks,
        )
        db.session.add(feedback)
        db.session.commit()

        ranking.feedback_id = feedback.id
        db.session.add(ranking)
        db.session.commit()

        rankings = db.session.query(Result).filter_by(tdi=ranking.id).all()
        for r in rankings:
            r.feedback_id = feedback.id
        db.session.add_all(rankings)
        db.session.commit()

        return jsonify({"msg": "Added new feedback with success!"}), 201


@api.route("/ranking/<int:rid>", methods=["GET"])
def ranking_from_db(rid):
    """Get a ranking by its result id from the database.
    Tested: true"""
    ranking = db.session.query(Result).get_or_404(rid)
    return Response(
        json.dumps(ranking.serialize, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )


@api.route("/ranking", methods=["GET"])
def ranking():
    """Produce a ranking for current session

    @return:    ranking result (dict)
                header contains meta-data
                body contains ranked document list
    """
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    query = request.args.get("query", None)
    if query is None:
        return "Missing query string", 400

    container_name = request.args.get("container", None)

    # fetch result from db if it exists
    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()

    # without a session ID we can not guarantee consistency and avoid showing different users the same results
    if session_exists:
        current_app.logger.debug(f"Session {session_id} exists, try to get cached")
        response = get_cached_response(query, page, session_id)
        if response:
            return Response(
                json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
                mimetype="application/json",
            )

    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(query)

    if not session_exists:
        current_app.logger.debug(f"Session {session_id} does not exist, create new")
        session_id = create_new_session(container_name, sid=session_id, type="ranker")

    response = asyncio.run(make_results(container_name, query, rpp, page, session_id))
    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
