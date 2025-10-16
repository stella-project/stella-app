import asyncio

from app.models import Session, db
from app.services.proxy_service import build_query_string, make_results
from app.services.result_service import get_cached_response
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import Response, current_app, json, request

from . import main


@main.route("/proxy/<path:url>", methods=["GET"])
def proxy(url):
    """
    Proxy endpoint for forwarding requests to retrieval systems.
    ---
    tags:
      - Proxy
    basePath: /
    description: |
      The `/proxy` endpoint is directly available at the root level and is not part of the standard STELLA API (`/stella/api/v1`).
      
      It forwards requests to the systems registered to the STELLA app.

      Experiment control parameters (`sid`, `container`, `system-type`, `page`, etc.) must be prefixed with `stella-` when calling this endpoint.
      
      Other query parameters are forwarded unchanged. Supports interleaved and non-interleaved experiments.
 
      **Supported STELLA parameters:**
      - **stella-container**: Name of the target container. If not provided, the least served system is used.
      - **stella-sid**: Session ID. If not provided or invalid, a new session is created.
      - **stella-system-type**: Type of system — either `ranking` or `retrieval`. Defaults to `ranking`.
      - **stella-page**: Optional page indicator for cached results.

      All other query parameters are forwarded unchanged to the underlying retrieval service.
    parameters:
      - name: url
        in: path
        type: string
        required: true
        description: The URL path (including subpaths) to forward the request to.
      - name: stella-container
        in: query
        type: string
        required: false
        description: Name of the container/system to which the request should be forwarded.
      - name: stella-sid
        in: query
        type: string
        required: false
        description: Existing session ID. If invalid or missing, a new session is created by STELLA.
      - name: stella-system-type
        in: query
        type: string
        required: false
        enum: [ranking, retrieval]
        default: ranking
        description: Type of system for the proxy request.
      - name: stella-page
        in: query
        type: integer
        required: false
        description: Page number for cached responses.
      - name: query_params
        in: query
        type: object
        additionalProperties:
          type: string
        required: false
        description: |
          Any other query parameters to forward to the underlying system (e.g., `query`, `page`, `rpp`, `sort`).
          Users can provide arbitrary key-value pairs here.
    responses:
      200:
        description: Successfully proxied the request to a retrieval system.
        schema:
          type: object
          description: |
            Returns the results from the target system(s). STELLA-specific metadata fields
            are prefixed with `stella-`, including `stella-sid`, `stella-rid`, `stella-q`,
            `stella-page`, `stella-rpp`, `stella-hits`, and `stella-container`.
      400:
        description: Invalid request parameters.
    """
    # extract stella specific parameters
    params = request.args.copy()  # copy to make them mutable
    system_type = params.pop("stella-system-type", "ranking")
    page = params.pop("stella-page", None)
    container_name = params.pop("stella-container", None)

    session_id = params.pop("stella-sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()

    query = build_query_string(url, params)

    # without a session ID we can not guarantee consistency and avoid showing different users the same results
    if session_exists:
        current_app.logger.debug(f"Session {session_id} exists, try to get cached")
        response = get_cached_response(query, page, session_id)
        if response:
            return Response(
                json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
                mimetype="application/json",
            )

    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(type="RANK" if system_type == "ranking" else "REC")

    if not session_exists:
        # TODO: `create_new_session` and `make_results` use different identifiers to distinguish ranking and recommendation systems. This should be unified.
        type = "ranker" if system_type == "ranking" else "recommendation"
        current_app.logger.debug(f"Session {session_id} does not exist, create new")
        session_id = create_new_session(container_name, sid=session_id, type=type)

    response = asyncio.run(
        make_results(container_name, session_id, url, params, system_type)
    )

    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
