import asyncio

from app.models import Feedback, Result, Session, db
from app.services.profile_service import profile_route
from app.services.result_service import make_results
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
    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(query)

    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()

    if not session_exists:
        session_id = create_new_session(container_name, type="ranker")

    response = asyncio.run(make_results(container_name, query, rpp, page, session_id))

    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )


@api.route("/ranking/proxy", methods=["GET"])
def ranking_proxy_request():
    """Ranking proxy endpoint. The endpoint passes the request including all query parameters to the systems that are compared. The parameters `page`, `rpp`, `sid`, and `container` are used to control the experiment if available. If they are not available, the default values `page=0` and `rpp=10` are used `container` falls back to the least served system and a new session is created for `sid`.

    TODO: The control parameters could be mapped by the system config so that, for example, existing session IDs could be reused.
    """
    # Use default values for page and rpp
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    query = str(request.args.to_dict())  # for logging only

    container_name = request.args.get("container", None)
    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(query)

    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()

    if not session_exists:
        session_id = create_new_session(container_name, type="ranker")

    response = asyncio.run(
        make_results(container_name, query, rpp, page, session_id, params=request.args)
    )

    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
