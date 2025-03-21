from app.models import Feedback, Result, Session, db
from app.services.recommendation_service import make_recommendation
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import jsonify, request
from pytz import timezone

from . import api

tz = timezone("Europe/Berlin")


@api.route("/recommendation/<int:id>/feedback", methods=["POST"])
def post_feedback_recommendations(id):
    """Add user feedback for recommendations."""
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

    if clicks is not None:
        recommendation = db.session.query(Result).get_or_404(id)

        feedback = Feedback(
            start=recommendation.q_date,
            session_id=recommendation.session_id,
            interleave=recommendation.tdi is not None,
            clicks=clicks,
        )
        db.session.add(feedback)
        db.session.commit()

        recommendation.feedback_id = feedback.id
        db.session.add(recommendation)
        db.session.commit()

        recommendations = db.session.query(Result).filter_by(tdi=recommendation.id).all()
        for r in recommendations:
            r.feedback_id = feedback.id
        db.session.add_all(recommendations)
        db.session.commit()

        return jsonify({"msg": "Added new feedback for recommendations successfully!"}), 201



@api.route("/recommendation/<int:rid>", methods=["GET"])
def recommendation_from_db(rid):
    """Get a recommendation by its result id from the database.
    Tested: true"""
    recommendation = db.session.query(Result).get_or_404(rid)
    return jsonify(recommendation.serialize)


@api.route("/recommendation", methods=["GET"])
def recommendation():
    """Produce a recommendation for current session

    @return:    recommendation result (dict)
                header contains meta-data
                body contains recommended document list
    """
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    item_id = request.args.get("itemid", None)
    if not item_id:
        return jsonify({"error": "Missing item ID"}), 400  
    container_name = request.args.get("container", None)
    if container_name is None:
        container_name = get_least_served_system(item_id)

    session_id = request.args.get("sid", None)
    if session_id is None or db.session.query(Session).filter_by(id=session_id) is None:
        session_id = create_new_session(container_name, type="recommender")

    response = make_recommendation(container_name, item_id, rpp, page, session_id)

    return jsonify(response)


