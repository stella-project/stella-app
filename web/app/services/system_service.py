import requests
from app.models import System, db
from flask import current_app


def rest_index(container_name):
    try:
        if current_app.config["SYSTEMS_CONFIG"][container_name].get("url"):
            # Use custom URL if provided in the config
            url = current_app.config["SYSTEMS_CONFIG"][container_name]["url"] + "/index"
        else:
            url = f"http://{container_name}:5000/index"
    except KeyError:
        msg = f"Container '{container_name}' not found in SYSTEMS_CONFIG."
        current_app.logger.error(msg)
        return 400, msg

    try:
        # Force a trusted Host value while still routing to the container URL
        response = requests.get(url, timeout=120, headers={"Host": "localhost"})
        if response.status_code >= 400:
            current_app.logger.error(
                "Indexing failed for '%s' (%s): %s %s",
                container_name,
                url,
                response.status_code,
                response.text,
            )
        else:
            current_app.logger.info(
                "Indexing succeeded for '%s' (%s): %s",
                container_name,
                url,
                response.status_code,
            )
        return response.status_code, response.text
    except requests.RequestException as exc:
        msg = f"Indexing request failed for '{container_name}' ({url}): {exc}"
        current_app.logger.error(msg)
        return 502, msg


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
            .filter(System.system_type == 'LIVE')
            .order_by(System.num_requests_no_head)
            .first()
            .name
        )
    return container_name
