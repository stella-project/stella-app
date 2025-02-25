import json
import time
from datetime import datetime
from uuid import uuid4
from . import api

import requests
from app.models import Feedback, Result, Session, System, db
from app.utils import create_dict_response
from flask import current_app, jsonify, request
from pytz import timezone

from app.services.session_service import create_new_session
from app.services.recommendation_service import query_system,build_response,request_recommendations
tz = timezone("Europe/Berlin")


@api.route("/recommendation", methods=["GET"])
def recommend():
    """Fetch recommendations from the unified container API.

    Returns:
        Response: A JSON response containing recommendations or an error message.
    """
    try:
        itemid = request.args.get("itemid")
        container_name = request.args.get("container")
        session_id = request.args.get("sid")
        page = request.args.get("page", default=0, type=int)
        rpp = request.args.get("rpp", default=10, type=int)

        if not itemid:
            return jsonify({"error": "Missing 'itemid' in request"}), 400

        if not container_name:
            system = System.query.order_by(System.num_requests).first()
            container_name = system.name if system else "default_container"

        if not session_id:
            session_id = create_new_session(container_name=container_name, type="recommender")

        recommendation_exp = query_system(container_name, itemid, rpp, page, session_id)

        if recommendation_exp is None:
            return jsonify({"message": f"No recommendations found for item '{itemid}'"}), 404

        return jsonify(build_response(recommendation_exp, container_name))

    except Exception as e:
        current_app.logger.error(f"Error in recommend: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route("/recommendation/<int:id>/feedback", methods=["POST"])
def post_rec_feedback(id: int):
    """Post feedback for recommendations."""
    clicks = request.values.get("clicks", None) or request.json.get("clicks", None)

    if clicks is not None:
        recommendation = Result.query.get_or_404(id)
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
        recommendations = Result.query.filter_by(tdi=recommendation.id).all()
        for r in recommendations:
            r.feedback_id = feedback.id
        db.session.add_all(recommendations)
        db.session.commit()
        return jsonify({"msg": "Feedback added successfully!"}), 201

@api.route("/recommendation/<int:rid>", methods=["GET"])
def get_recommendation_by_id(rid: int):
    """Fetch a specific recommendation by its ID."""
    try:
        from app.models import Result
        print(Result.query.all())  

        recommendation = Result.query.get_or_404(rid)
        return jsonify(recommendation.serialize)
    except Exception as e:
        current_app.logger.error(f"Error fetching recommendation {rid}: {str(e)}")
        return jsonify({"error": f"Could not fetch recommendation {rid}"}), 500
