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

tz = timezone("Europe/Berlin")


### Fetch Both Dataset and Publication Recommendations ###
def fetch_recommendations(container_name: str, item_id: str, rpp: int, page: int) -> dict:
    """Fetch both dataset and publication recommendations from the unified /recommendation endpoint.

    Args:
        container_name (str): The name of the container providing recommendations.
        item_id (str): The ID of the item for which recommendations are requested.
        rpp (int): Results per page.
        page (int): Page number.

    Returns:
        dict: A dictionary containing merged dataset and publication recommendations.
    """
    url = f"http://{container_name}:5000/recommendation"
    params = {"item_id": item_id, "rpp": rpp, "page": page}

    current_app.logger.debug(f"Fetching recommendations from {url}")

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        return result

    except requests.Timeout:
        current_app.logger.error(f"Timeout error when contacting {url}")
        return {"itemlist": [], "num_found": 0, "error": "Timeout"}

    except requests.RequestException as e:
        current_app.logger.error(f"Error in fetch_recommendations: {str(e)}")
        return {"itemlist": [], "num_found": 0, "error": str(e)}


### Query System for Recommendations ###
def query_system(container_name: str, item_id: str, rpp: int, page: int, session_id: int, type: str = "EXP") -> Result:
    """Query the recommendation system and store merged dataset + publication recommendations.

    Args:
        container_name (str): The name of the container providing recommendations.
        item_id (str): The ID of the item for which recommendations are requested.
        rpp (int): Results per page.
        page (int): Page number.
        session_id (int): The session ID for tracking recommendations.
        type (str, optional): Type of recommendation (Default: "EXP").

    Returns:
        Result: A Result object containing the recommendation data, or None if no recommendations found.
    """
    try:
        current_app.logger.debug(f'Querying "{container_name}" for recommendations...')
        q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
        ts_start = time.time()

        system = System.query.filter_by(name=container_name).first()
        if not system:
            raise ValueError(f"System '{container_name}' not found in the database.")

        # Fetch recommendations from unified `/recommendation` endpoint
        result = fetch_recommendations(container_name, item_id, rpp, page)

        if not result["itemlist"]:
            current_app.logger.warning(f"No recommendations found for item '{item_id}'")
            return None

        q_time = round((time.time() - ts_start) * 1000)
        num_found = result["num_found"]
        item_dict = {i + 1: {"docid": doc, "type": type} for i, doc in enumerate(result["itemlist"])}

        recommendation = Result(
            session_id=session_id,
            system_id=system.id,
            type="REC_COMBINED",
            q=item_id,
            q_date=q_date,
            q_time=q_time,
            num_found=num_found,
            page=page,
            rpp=rpp,
            items=item_dict,
        )

        db.session.add(recommendation)
        db.session.commit()

        return recommendation

    except Exception as e:
        current_app.logger.error(f"Error in query_system: {str(e)}")
        return None


### Unified Recommendation API Endpoint ###
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

        if not itemid:
            return jsonify({"error": "Missing 'itemid' in request"}), 400

        # Fetch existing session recommendation
        if session_id and itemid:
            recommendation = Result.query.filter_by(session_id=session_id, q=itemid).first()
            if recommendation:
                if recommendation.tdi:
                    recommendation = Result.query.filter_by(id=recommendation.tdi).first()

                system_id = Session.query.filter_by(id=session_id).first().system_recommendation
                container_name = System.query.filter_by(id=system_id).first().name

                response = {
                    "header": {
                        "sid": recommendation.session_id,
                        "rid": recommendation.id,
                        "itemid": itemid,
                        "container": {"exp": container_name},
                    },
                    "body": recommendation.items,
                }
                return jsonify(response)

        # Fetch new recommendations
        page = request.args.get("page", default=0, type=int)
        rpp = request.args.get("rpp", default=10, type=int)

        if not container_name:
            system = System.query.order_by(System.num_requests).first()
            container_name = system.name if system else "default_container"

        if not session_id:
            session_id = create_new_session(container_name=container_name, type="recommender")

        recommendation_exp = query_system(container_name, itemid, rpp, page, session_id)

        if recommendation_exp is None:
            return jsonify({"message": f"No recommendations found for item '{itemid}'"}), 404

        response = {
            "header": {
                "sid": recommendation_exp.session_id,
                "rid": recommendation_exp.id,
                "itemid": itemid,
                "container": {"exp": container_name},
            },
            "body": recommendation_exp.items,
        }
        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f"Error in recommend: {str(e)}")
        return jsonify({"error": str(e)}), 500


### Feedback API ###
@api.route("/recommendation/<int:id>/feedback", methods=["POST"])
def post_rec_feedback(id: int):
    """Post feedback for recommendations.

    Args:
        id (int): The ID of the recommendation.

    Returns:
        Response: A JSON response confirming feedback submission.
    """
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

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


### Get Recommendation by ID ###
@api.route("/recommendation/<int:rid>", methods=["GET"])
def get_recommendation_by_id(rid: int):
    """Fetch a specific recommendation by its ID.

    Args:
        rid (int): The ID of the recommendation.

    Returns:
        Response: A JSON response containing the recommendation data.
    """
    try:
        recommendation = Result.query.get_or_404(rid)
        return jsonify(recommendation.serialize)
    except Exception as e:
        current_app.logger.error(f"Error fetching recommendation {rid}: {str(e)}")
        return jsonify({"error": f"Could not fetch recommendation {rid}"}), 500
