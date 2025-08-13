import asyncio
from typing import Tuple

from app.models import Feedback, Result, Session, db
from app.services.result_service import make_results
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import Response, current_app, jsonify, request, json
from pytz import timezone

from . import api

tz = timezone("Europe/Berlin")


@api.route("/recommendation/<int:id>/feedback", methods=["POST"])
def post_feedback_rec(id: str) -> Tuple[Response, int]:
    """Add interaction feedback for a ranking id to the database.

    Args:
        id (int): ID of the results object in the database.

    Returns:
        Tuple[Response, int]: A tuple where the first element is a Flask JSON response containing a status message, and the second is the HTTP status code (201 or 400).
    """
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

    if clicks:
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

        recommendations = db.session.query(Result).filter_by(tdi=ranking.id).all()
        for r in recommendations:
            r.feedback_id = feedback.id
        db.session.add_all(recommendations)
        db.session.commit()

        return jsonify({"msg": "Added new feedback with success!"}), 201
    else:
        return jsonify({"msg": "No feedback provided!"}), 400


@api.route("/recommendation/<int:id>", methods=["GET"])
def ranking_from_db_rec(id: str) -> Tuple[Response, int]:
    """Get a ranking by its result id from the database.

    Args:
        id (str): ID of the results object in the database.

    Returns:
        Tuple[Response, int]: A tuple where the first element is a Flask JSON response containing a status message, and the second is the HTTP status code (201 or 400).
    """
    ranking = db.session.query(Result).get_or_404(id)
    return Response(json.dumps(ranking.serialize, sort_keys=False, ensure_ascii=False, indent=2), mimetype='application/json')


@api.route("/recommendation", methods=["GET"])
def recommendation():
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    # Item
    itemid = request.args.get("itemid", None)
    if itemid is None:
        return "Missing itemid", 400

    # System
    container_name = request.args.get("container", None)
    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(query=itemid, type="REC")

    # Session
    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()
    if not session_exists:
        session_id = create_new_session(container_name, type="recommendation")

    response = asyncio.run(
        make_results(
            container_name,
            itemid,
            rpp,
            page,
            session_id,
            system_type="recommendation",
        )
    )

    return Response(json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2), mimetype='application/json')

@api.route("/recommendation/proxy", methods=["GET"])
def recommendation_proxy_request():
    """Recommendation proxy endpoint. The endpoint passes the request including all query parameters to the systems that are compared. The parameters `page`, `rpp`, `sid`, and `container` are used to control the experiment if available. If they are not available, the default values `page=0` and `rpp=10` are used `container` falls back to the least served system and a new session is created for `sid`.

    TODO: The control parameters could be mapped by the system config so that, for example, existing session IDs could be reused.
    """
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    # Item
    itemid = request.args.get("itemid", None)
    if itemid is None:
        return "Missing itemid", 400

    # System
    container_name = request.args.get("container", None)
    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(query=itemid, type="REC")

    # Session
    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()
    if not session_exists:
        session_id = create_new_session(container_name, type="recommendation")

    response = asyncio.run(
        make_results(
            container_name,
            itemid,
            rpp,
            page,
            session_id,
            system_type="recommendation",
            params=request.args
        )
    )

    return Response(json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2), mimetype='application/json')