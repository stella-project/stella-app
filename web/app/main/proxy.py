import asyncio

from app.models import Feedback, Result, Session, db
from app.services.proxy_service import make_results
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import Flask, Response, current_app, json, jsonify, request

from . import main


@main.route("/proxy/<path:url>", methods=["GET"])
def proxy(url):
    """Proxy endpoint that directly forwards the request including sub-paths and parameters to the retrieval systems. Only the parameters starting with `stella-` are used by STELLA itself and removed before forwarding the request:
    - `stella-container`: Name of the container to which the request should be forwarded. If not provided, the least served system is chosen.
    - `stella-sid`: Session ID. If not provided or invalid, a new session is created. If no session_id or container name is provided consistent results across a session can not be ensured.
    - `stella-system-type`: Type of the system, either `ranking` or `retrieval`. Defaults to `ranking`. This is to determine the pool of systems for interleaving.

    Args:
        url (str): The URL path to proxy the request to.

    Returns:
        Response: The response from the proxied request.
    """
    params = request.args.copy()  # copy to make them mutable
    system_type = params.get("stella-system-type", "ranking")

    # extract stella specific parameters
    container_name = params.pop("stella-container", None)
    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system()

    session_id = params.pop("stella-sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()
    if not session_exists:
        session_id = create_new_session(container_name, sid=session_id, type="ranker")

    response = asyncio.run(
        make_results(container_name, session_id, url, params, system_type=system_type)
    )
    current_app.logger.debug(f"Params: {params}")
    current_app.logger.debug(f"Type of params: {type(params)}")

    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
