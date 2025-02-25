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
    response = requests.get(
        f"http://{container_name}:5000/recommendation",
        params={"item_id": item_id, "rpp": rpp, "page": page},
    )
    return response.json()

def query_system(container_name, item_id, rpp, page, session_id, type="EXP"):
    """
    Query the recommendation system and store recommendations.
    """
    current_app.logger.debug(f'Fetching recommendations from system: "{container_name}"...')
    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()
    
    system = db.session.query(System).filter_by(name=container_name).first()
    if not system:
        raise ValueError(f"System '{container_name}' not found in database.")
    
    result = request_recommendations(container_name, item_id, rpp, page)
    
    ts_end = time.time()
    q_time = round((ts_end - ts_start) * 1000)
    num_found = result.get("num_found", 0)
    
    item_dict = {
        i + 1: {"docid": doc, "type": type} for i, doc in enumerate(result.get("itemlist", []))
    }
    
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

def build_response(recommendation, container_name):
    """
    Build response structure for recommendations.
    """
    return {
        "header": {
            "sid": recommendation.session_id,
            "rid": recommendation.id,
            "itemid": recommendation.q,
            "container": {"exp": container_name},
        },
        "body": recommendation.items,
    }