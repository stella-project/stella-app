import asyncio
from datetime import datetime

from app.models import Feedback, Result, Session, System, db
from app.services.profile_service import profile_route
from app.services.result_service import get_cached_response, make_results
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import Response, current_app, json, jsonify, request
from pytz import timezone

from . import api

tz = timezone("Europe/Berlin")


@api.route("/ranking/<int:id>/feedback", methods=["POST"])
def post_feedback(id):
    """
    Send ranking user feedback to STELLA database.
    ---
    tags:
      - Feedback
    description: |
        Sends user interaction feedback to STELLA APP database for a given ranking result ID.

        The feedback captures:
        - Which ranked items were **clicked** by the user.
        - The **start** and **end timestamps** of the interaction session.
        - Whether the session used **interleaving** (comparison between two systems).

        #### 🧩 Payload Structure
        The request must include the following top-level fields:
        - **clicks** *(object, required)* — A mapping of rank positions (as strings) to interaction details.
        - **start** *(string, required)* — ISO-like timestamp indicating when the session started.
        - **end** *(string, required)* — ISO-like timestamp indicating when the session ended.
        - **interleave** *(boolean, required)* — Whether this session used interleaved results.

      
        #### 🖱️ Clicks object structure
        Each key corresponds to a rank position ("1", "2", ...), and the value contains:
        - **clicked** *(bool)* — Whether the item was clicked.
        - **date** *(string | null)* — Timestamp of click event or `null` if not clicked.
        - **docid** *(string)* — Unique document identifier (e.g., internal ID).
        - **type** *(string)* — Source type (`"BASE"` or `"EXP"`) indicating which system produced it.
    
        **Example curl:**
        ```bash
        curl -X POST "http://localhost:8080/stella/api/v1/ranking/3/feedback" \\
            -H "Content-Type: application/json" \\
            -d '{
            "clicks": {
                "1": {"clicked": false, "date": null, "docid": "M26923455", "type": "EXP"},
                "2": {"clicked": true, "date": "2020-07-29 16:06:51", "docid": "M27515393", "type": "BASE"}
            },
            "start": "2020-07-29 16:06:51",
            "end": "2020-07-29 16:12:53",
            "interleave": true
            }'
        ```

    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Unique identifier of the ranking result.
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - clicks
            - start
            - end
            - interleave
          properties:
            clicks:
              type: object
              description: Mapping of ranking positions to click metadata.
            start:
              type: string
              format: date-time
              example: "2020-07-29 16:06:51"
            end:
              type: string
              format: date-time
              example: "2020-07-29 16:12:53"
            interleave:
              type: boolean
              example: true
    responses:
      201:
        description: Feedback added successfully
        schema:
          type: object
          properties:
            msg:
              type: string
              example: Added new feedback with success!
      400:
        description: No feedback provided. Bad request (missing clicks)
    """
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

    if clicks is not None:
        ranking = db.session.query(Result).get_or_404(id)

        feedback = Feedback(
            start=ranking.q_date,
            session_id=ranking.session_id,
            interleave=ranking.tdi is not None,
            clicks=clicks,
        )
        db.session.add(feedback)
        db.session.commit()

        ranking.feedback_id = feedback.id
        db.session.add(ranking)
        db.session.commit()

        rankings = db.session.query(Result).filter_by(tdi=ranking.id).all()
        for r in rankings:
            r.feedback_id = feedback.id
        db.session.add_all(rankings)
        db.session.commit()

        return jsonify({"msg": "Added new feedback with success!"}), 201
    else:
        return jsonify({"msg": "No feedback provided!"}), 400

@api.route("/ranking/<int:rid>", methods=["GET"])
def ranking_from_db(rid):
    """
    Get a ranking by its result ID from the database.
    ---
    tags:
      - Ranking
    description: |
      Returns the ranking data stored in the database for a given result ID.
      The response includes metadata and the ranked document list.
    parameters:
      - name: rid
        in: path
        type: integer
        required: true
        description: Ranking ID for which the rankings are to be retrieved.
    responses:
      200:
        description: Ranking successfully retrived for the ID.
        examples:
          application/json:
            header:
                container:
                    base: "rank_elastic_base"
                    exp: "rank_elastic"
                page: 0
                q: "vaccine"
                rid: 3
                rpp: 20
                hits: 12312
                sid: 1
            body:
                "1": {"docid": "M27622217", "type": "BASE"}
                "2": {"docid": "M27251231", "type": "EXP"}
                "3": {"docid": "M27692969", "type": "BASE"}
                "4": {"docid": "M26350569", "type": "EXP"}
      404:
        description: Ranking not found for the given ID.
    """
    ranking = db.session.query(Result).get_or_404(rid)
    return Response(
        json.dumps(ranking.serialize, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )


@api.route("/ranking", methods=["GET"])
def ranking():
    """
    Generate rankings for a given query and session.
    ---
    tags:
      - Ranking
    description: |
        Returns a ranked list of documents for the specified query and session ID.
        If cached results exist, they are returned directly. Otherwise, a new session and ranking are created.
        If no session ID is provided, STELLA automatically generates a new session ID.
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: Search query string.
      - name: page
        in: query
        type: integer
        required: false
        description: Page number for pagination.
      - name: rpp
        in: query
        type: integer
        required: false
        description: Results per page.
      - name: sid
        in: query
        type: string
        required: false
        description: Session ID. If not provided, a new session is automatically created by STELLA.
      - name: container
        in: query
        type: string
        required: false
        description: Name of the container/system to use for generating results.
    responses:
      200:
        description: Ranking successfully generated.
        examples:
          application/json:
            header:
                container:
                    base: "rank_elastic_base"
                    exp: "rank_elastic"
                page: 0
                q: "vaccine"
                rid: 3
                rpp: 20
                hits: 12312
                sid: 1
            body:
                "1": {"docid": "M27622217", "type": "BASE"}
                "2": {"docid": "M27251231", "type": "EXP"}
                "3": {"docid": "M27692969", "type": "BASE"}
                "4": {"docid": "M26350569", "type": "EXP"}
            
      400:
        description: Missing query string or invalid parameters.
    """
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    query = request.args.get("query", None)
    if query is None:
        return "Missing query string", 400

    container_name = request.args.get("container", None)

    # fetch result from db if it exists
    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()

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
        container_name = get_least_served_system(query)

    if not session_exists:
        current_app.logger.debug(f"Session {session_id} does not exist, create new")
        session_id = create_new_session(container_name, sid=session_id, type="ranker")

    response = asyncio.run(make_results(container_name, query, rpp, page, session_id))
    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
