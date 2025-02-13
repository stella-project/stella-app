import requests

from flask import current_app
from app.models import db, System


def rest_index(container_name):
    requests.get(f"http://{container_name}:5000/index")


def get_least_served_system(query):
    if query in current_app.config["HEAD_QUERIES"]:
        container_name = (
            db.session.query(System)
            .filter(System.name != current_app.config["RANKING_BASELINE_CONTAINER"])
            .filter(
                System.name.notin_(
                    current_app.config["RECOMMENDER_CONTAINER_NAMES"]
                    + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
                )
            )
            .order_by(System.num_requests)
            .first()
            .name
        )
    else:
        # Select least served container
        container_name = (
            db.session.query(System)
            .filter(System.name != current_app.config["RANKING_BASELINE_CONTAINER"])
            .filter(
                System.name.notin_(
                    current_app.config["RECOMMENDER_CONTAINER_NAMES"]
                    + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
                    + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
                )
            )
            .order_by(System.num_requests_no_head)
            .first()
            .name
        )
    return container_name
