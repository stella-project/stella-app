import json
import time
from datetime import datetime

import requests
from app.extensions import cache
from app.models import Result, System, db
from app.services.interleave_service import interleave_results
from flask import current_app
from pytz import timezone

tz = timezone("Europe/Berlin")


def request_recommendations_from_container(container_name, item_id, rpp, page):
    """
    Fetch recommendations from a given container via REST API.
    """
    try:
        response = requests.get(
            f"http://{container_name}:5000/recommendation",
            params={"item_id": item_id, "rpp": rpp, "page": page},
        )

        if response.status_code != 200 or not response.content.strip():
            current_app.logger.error(f"ERROR: Failed request to {container_name}, status: {response.status_code}")
            return {}

        data = response.json()

        #  Debug log to check response
        current_app.logger.debug(f"DEBUG: API Response from {container_name}: {json.dumps(data, indent=4)}")

        if "itemlist" not in data:
            current_app.logger.error(f"ERROR: Missing 'itemlist' in API response from {container_name}")
            return {}

        return data

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"ERROR: Request failed: {str(e)}")
        return {}

    except json.JSONDecodeError:
        current_app.logger.error(f"ERROR: Invalid JSON response from {container_name}")
        return {}


def query_system(container_name, item_id, rpp, page, session_id, type="EXP"):
    """
    Query the recommendation system and store recommendations.
    """
    current_app.logger.debug(f'Fetching recommendations from "{container_name}" for item "{item_id}"...')
    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()

    system = db.session.query(System).filter_by(name=container_name).first()
    if not system:
        current_app.logger.error(f"ERROR: System '{container_name}' not found in database.")
        return None, None

    result = request_recommendations_from_container(container_name, item_id, rpp, page)

    ts_end = time.time()
    q_time = round((ts_end - ts_start) * 1000)

    itemlist = result.get("itemlist", [])
    if not isinstance(itemlist, list):
        current_app.logger.error(f"ERROR: Expected 'itemlist' to be a list, got {type(itemlist)}")
        return None, None

    recommendation = Result(
        session_id=session_id,
        system_id=system.id,
        type="REC",
        q=item_id,
        q_date=q_date,
        q_time=q_time,
        num_found=len(itemlist),
        page=page,
        rpp=rpp,
        items=json.dumps(itemlist),  # Store as JSON string
    )
    db.session.add(recommendation)
    db.session.commit()

    return recommendation, result


def build_response(
    recommendation,
    container_name,
    interleaved_recommendation=None,
    recommendation_base=None,
    container_name_base=None,
    result=None,
    result_base=None,
):
    """Builds the response object for recommendations. Handles interleaving."""

    def build_id_map(container_name, recommendation, result):
        """Build the docid ranking position map to construct passthrough responses from interleaved recommendations."""
        if isinstance(result, str):
            try:
                result = json.loads(result)  # Deserialize JSON if it's a string
            except json.JSONDecodeError:
                current_app.logger.error(f"ERROR: Failed to decode result JSON for {container_name}")
                return {}

        if "itemlist" in result:
            return {
                str(i + 1): {"docid": doc, "type": "EXP"}  # Convert list to dict format
                for i, doc in enumerate(result["itemlist"])
            }

        return {}

    def build_header(recommendation_obj, container_names):
        """Helper function to build the response header."""
        return {
            "sid": recommendation_obj.session_id,
            "rid": getattr(recommendation_obj, "tdi", -1),
            "q": recommendation_obj.q,
            "page": recommendation_obj.page,
            "rpp": recommendation_obj.rpp,
            "hits": recommendation_obj.num_found,
            "container": container_names,
        }

    def build_simple_response(recommendation_obj):
        """Helper function to build a simple response when no interleaving."""
        container_names = {"exp": container_name}

        # Ensure `recommendation_obj.items` is a dict and not a JSON string
        if isinstance(recommendation_obj.items, str):
            try:
                recommendation_obj.items = json.loads(recommendation_obj.items)
            except json.JSONDecodeError:
                current_app.logger.error("ERROR: Failed to decode recommendation items JSON")
                recommendation_obj.items = {}

        # Convert list to expected dictionary format
        formatted_body = {
            str(i + 1): {"docid": doc, "type": "EXP"} for i, doc in enumerate(recommendation_obj.items)
        }

        return {
            "header": build_header(recommendation_obj, container_names),
            "body": formatted_body,  # Updated format
        }

    if not interleaved_recommendation:
        return build_simple_response(recommendation)

    # If interleaved_recommendation is provided
    id_map = build_id_map(
        current_app.config["RECOMMENDER_BASELINE_CONTAINER"], recommendation_base, result_base
    )
    id_map.update(build_id_map(container_name, recommendation, result))

    hits = [id_map.get(doc["docid"], {"docid": doc["docid"], "type": "EXP"}) for doc in interleaved_recommendation.items.values()]

    container_names = {"exp": container_name, "base": container_name_base}
    return {
        "header": build_header(recommendation_base, container_names),
        "body": hits,
    }


def make_recommendation(container_name, item_id, rpp, page, session_id):
    """
    Generate recommendations, including interleaved recommendations if configured.
    """
    recommendation, result = query_system(
        container_name, item_id, rpp, page, session_id, type="EXP"
    )

    if current_app.config["INTERLEAVE"]:
        current_app.logger.info("Interleaving recommendations")
        recommendation_base, result_base = query_system(
            current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
            item_id,
            rpp,
            page,
            session_id,
            type="BASE",
        )

        if recommendation_base is None:
            current_app.logger.error(f"ERROR: query_system() returned None for baseline recommendations")
            return {"error": "Baseline recommendations not available"}, 500

        interleaved_recommendation = interleave_results(recommendation, recommendation_base,type="REC")

        response = build_response(
            recommendation,
            container_name,
            interleaved_recommendation,
            recommendation_base,
            current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
            result,
            result_base,
        )

    else:
        response = build_response(recommendation, container_name, result=result)

    return response
