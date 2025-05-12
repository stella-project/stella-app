import requests
from app.models import System, db
from flask import current_app


def rest_index(container_name):
    requests.get(f"http://{container_name}:5000/index")


def get_least_served_system(query: str = "", type: str = "RANK") -> str:
    """Get the least served system of a given system type. If a query is provided, it is first checked if a precomputed system is available for that query.

    Args:
        query (str, optional): Query to check for precomputed runs. Defaults to "".
        type (str, optional): System type. Either RANK or REC. Defaults to "RANK".

    Returns:
        str: Name of the least served system.
    """
    if type == "RANK":
        exclude_systems = (
            [current_app.config["RANKING_BASELINE_CONTAINER"]]
            + [current_app.config["RECOMMENDER_BASELINE_CONTAINER"]]
            + current_app.config["RECOMMENDER_CONTAINER_NAMES"]
            + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
            + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
        )
    elif type == "REC":
        exclude_systems = (
            [current_app.config["RANKING_BASELINE_CONTAINER"]]
            + [current_app.config["RECOMMENDER_BASELINE_CONTAINER"]]
            + current_app.config["RANKING_CONTAINER_NAMES"]
            + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
            + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
        )

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
            .filter(System.name.notin_(exclude_systems))
            .order_by(System.num_requests_no_head)
            .first()
            .name
        )
    return container_name
