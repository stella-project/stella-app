import asyncio
from typing import Tuple

from app.models import Feedback, Result, Session, db
from app.services.result_service import get_cached_response, make_results
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from flask import Response, current_app, json, jsonify, request
from pytz import timezone

from . import api

tz = timezone("Europe/Berlin")


@api.route("/recommendation/<int:id>/feedback", methods=["POST"])
def post_feedback_rec(id: str) -> Tuple[Response, int]:
    """
    Send recommendation user feedback to STELLA database.
    ---
    tags:
      - Feedback
    description: |
      Stores user interaction feedback to STELLA APP database for a given recommendation result ID.
      
      The feedback captures:
      - Which recommended items were **clicked** by the user.
      - The **start** and **end timestamps** of the interaction session.
      - Whether the session used **interleaving** (comparison between two systems).

      #### 🧩 Payload Structure
      The request must include the following top-level fields:
      - **clicks** *(object, required)* — A mapping of recommendation positions (as strings) to interaction details.
      - **start** *(string, required)* — ISO-like timestamp indicating when the session started.
      - **end** *(string, required)* — ISO-like timestamp indicating when the session ended.
      - **interleave** *(boolean, required)* — Whether this session used interleaved results.

      
      #### 🖱️ Clicks object structure
      Each key corresponds to a recommendation position ("1", "2", ...), and the value contains:
      - **clicked** *(bool)* — Whether the item was clicked.
      - **date** *(string | null)* — Timestamp of click event or `null` if not clicked.
      - **docid** *(string)* — Unique document identifier (e.g., internal ID).
      - **type** *(string)* — Source type (`"BASE"` or `"EXP"`) indicating which system produced it.

        
       **Example curl:**
        ```bash
        curl -X POST "http://localhost:8080/stella/api/v1/recommendation/3/feedback" \\
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
        description: Unique identifier of the recommendation result.
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
              description: Mapping of recommendation positions to click metadata.
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
        description: Feedback added successfully.
        schema:
          type: object
          properties:
            msg:
              type: string
              example: Added new feedback with success!
      400:
        description: No feedback provided or invalid request.
        schema:
          type: object
          properties:
            msg:
              type: string
              example: No feedback provided. Bad request (missing clicks)
    """
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

    if clicks:
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

        recommendations = db.session.query(Result).filter_by(tdi=ranking.id).all()
        for r in recommendations:
            r.feedback_id = feedback.id
        db.session.add_all(recommendations)
        db.session.commit()

        return jsonify({"msg": "Added new feedback with success!"}), 201
    else:
        return jsonify({"msg": "No feedback provided!"}), 400


@api.route("/recommendation/<int:id>", methods=["GET"])
def ranking_from_db_rec(id: str) -> Tuple[Response, int]:
    """
    Get a recommendation result by its ID from the database.
    ---
    tags:
      - Recommendation
    description: |
      Returns a serialized recommendation result object stored in the database for the given ID.
      The response includes metadata and the ranked document list.
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID of the item for which recommendations are to be retrieved.
    responses:
      200:
        description: Successfully retrieved recommendation results for the ID.
        examples:
          application/json:
            header:
                container:
                    base: "recom_tfidf_base"
                    exp: "recom_tfidf"
                page: 0
                itemid: "M26923455"
                rid: 4
                rpp: 20
                hits: 24
                sid: 2
            body:
                "1": {"docid": "M27622217", "type": "BASE"}
                "2": {"docid": "M27251231", "type": "EXP"}
                "3": {"docid": "M27692969", "type": "BASE"}
                "4": {"docid": "M26350569", "type": "EXP"}
      404:
        description: Recommendation not found for the given ID.
    """
    ranking = db.session.query(Result).get_or_404(id)
    return Response(
        json.dumps(ranking.serialize, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )


@api.route("/recommendation", methods=["GET"])
def recommendation():
    """
    Generate recommendations for a given item and session.
    ---
    tags:
      - Recommendation
    description: |
      Returns a list of recommended items for a given input item and session ID.
      If cached recommendations exist, they are returned directly. Otherwise, a new session and recommendation are created.
      If no session ID is provided, STELLA automatically generates a new session ID.
    parameters:
      - name: itemid
        in: query
        type: string
        required: true
        description: ID of the item for which recommendations are generated.
      - name: page
        in: query
        type: integer
        required: false
        description: Page number for pagination.
      - name: rpp
        in: query
        type: integer
        required: false
        description: Number of recommendations per page.
      - name: sid
        in: query
        type: string
        required: false
        description: Session ID. If not provided, a new session is automatically created by STELLA.
      - name: container
        in: query
        type: string
        required: false
        description: Name of the container/system to use for generating recommendations.
    responses:
      200:
        description: Recommendation successfully generated.
        examples:
          application/json:
            header:
                container:
                    base: "recom_tfidf_base"
                    exp: "recom_tfidf"
                page: 0
                itemid: "M26923455"
                rid: 4
                rpp: 20
                hits: 24
                sid: 2
            body:
                "1": {"docid": "M27622217", "type": "BASE"}
                "2": {"docid": "M27251231", "type": "EXP"}
                "3": {"docid": "M27692969", "type": "BASE"}
                "4": {"docid": "M26350569", "type": "EXP"}
      400:
        description: Missing itemid or invalid query parameters.
    """
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    # Item
    itemid = request.args.get("itemid", None)
    if itemid is None:
        return "Missing itemid", 400

    # System
    container_name = request.args.get("container", None)

    # fetch result from db if it exists
    session_id = request.args.get("sid", None)
    session_exists = db.session.query(Session).filter_by(id=session_id).first()

    if session_exists:
        current_app.logger.debug(f"Session {session_id} exists, try to get cached")
        response = get_cached_response(itemid, page, session_id)
        if response:
            return Response(
                json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
                mimetype="application/json",
            )

    if container_name is None:
        current_app.logger.debug("No container name provided")
        container_name = get_least_served_system(query=itemid, type="REC")

    if not session_exists:
        current_app.logger.debug(f"Session {session_id} does not exist, create new")
        session_id = create_new_session(
            container_name, sid=session_id, type="recommendation"
        )

    response = asyncio.run(
        make_results(
            container_name,
            itemid,
            rpp,
            page,
            session_id,
            system_type="recommendation",
        )
    )

    return Response(
        json.dumps(response, sort_keys=False, ensure_ascii=False, indent=2),
        mimetype="application/json",
    )
