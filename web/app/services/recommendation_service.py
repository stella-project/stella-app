### app/services/recommendation_service.py
import json
import time
from datetime import datetime
from flask import current_app
from pytz import timezone
import requests
from app.models import Result, System, db

tz = timezone("Europe/Berlin")

def request_recommendations(container_name, item_id, rpp, page):
    """
    Fetch recommendations from a given container.
    """
    try:
        response = requests.get(
            f"http://{container_name}:5000/recommendation",
            params={"item_id": item_id, "rpp": rpp, "page": page},
        )

        if response.status_code != 200:
            current_app.logger.error(f"ERROR: Failed request to {container_name}, status: {response.status_code}")
            return {}

        data = response.json()

        # DEBUG: Log API response
        current_app.logger.debug(f"DEBUG: API Response from {container_name}: {json.dumps(data, indent=4)}")

        return data
    except Exception as e:
        current_app.logger.error(f"ERROR: Exception in request_recommendations: {str(e)}")
        return {}

def query_system(container_name, item_id, rpp, page, session_id, type="EXP"):
    """
    Query the recommendation system and store recommendations.
    """
    current_app.logger.debug(f'Fetching recommendations from system: "{container_name}" for item "{item_id}"...')

    # Make API call to recommendation system
    result = request_recommendations(container_name, item_id, rpp, page)

    # DEBUG: Print full response from API
    current_app.logger.debug(f"DEBUG: Raw API Response from {container_name}: {json.dumps(result, indent=4)}")

    # Step 1: Check if the response exists
    if not result:
        current_app.logger.error(f"ERROR: Empty response from {container_name}")
        return {"header": {"sid": session_id, "rid": -1, "itemid": item_id, "container": {"exp": container_name}}, "body": {}}

    # Step 2: Check if "body" exists in response
    if "itemlist" in result:  # Convert itemlist to body
        result["body"] = {i+1: {"docid": doc, "type": type} for i, doc in enumerate(result["itemlist"])}
        del result["itemlist"]  # Remove old itemlist key

    if "body" not in result or not isinstance(result["body"], dict) or len(result["body"]) == 0:
        current_app.logger.warning(f"WARNING: No recommendations found in '{container_name}' for item '{item_id}'")
        return {
            "header": {"sid": session_id, "rid": -1, "itemid": item_id, "container": {"exp": container_name}},
            "body": {},
        }

    # Step 3: Check if body contains recommendations
    if not isinstance(result["body"], dict) or len(result["body"]) == 0:
        current_app.logger.warning(f"WARNING: No recommendations found in '{container_name}' for item '{item_id}'")
        return {"header": {"sid": session_id, "rid": -1, "itemid": item_id, "container": {"exp": container_name}}, "body": {}}

    # Extract recommendations
    recommendation_items = result["body"]

    # Log valid recommendations
    current_app.logger.debug(f"SUCCESS: Received {len(recommendation_items)} recommendations from {container_name}")

    return {
        "header": {"sid": session_id, "rid": -1, "itemid": item_id, "container": {"exp": container_name}},
        "body": recommendation_items,
    }

def build_response(recommendation, container_name):
    """
    Build response structure for recommendations.
    """
    return {
        "header": recommendation.get("header", {
            "sid": "unknown-session",
            "rid": -1,
            "itemid": "unknown-item",
            "container": {"exp": container_name},
        }),
        "body": recommendation.get("body", {}),
    }
