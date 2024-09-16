import docker
import time
from flask import jsonify, request, current_app
from app import api
from app.models import db, Session, System, Result, Feedback
from app.services.interleave_service import interleave_rankings
from app.utils import create_dict_response
from pytz import timezone
from . import api
from app.services.session_service import create_new_session
from app.services.ranking_service import query_system, build_response

client = docker.DockerClient(base_url="unix://var/run/docker.sock")
tz = timezone("Europe/Berlin")


@api.route("/test/<string:container_name>", methods=["GET"])
def test(container_name):
    """
    Use the Docker client to execute a test script on an experimental system in a container

    @param container_name:  container name (str)

    @return: Test-Message (str)
    """
    container = client.containers.get(container_name)
    cmd = "python3 /script/test"
    out = container.exec_run(cmd)
    return "<h1> " + out.output.decode("utf-8") + " </h1>"


@api.route("/ranking/<int:id>/feedback", methods=["POST"])
def post_feedback(id):
    """Add user feedback to database (collect data for statistics)
    Tested: True

    @param id:  ranking id (int)
    @return:    HTTP status message
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


@api.route("/ranking/<int:rid>", methods=["GET"])
def ranking_from_db(rid):
    """Get a ranking by its result id from the database.
    Tested: true"""
    ranking = db.session.query(Result).get_or_404(rid)
    return jsonify(ranking.serialize)


@api.route("/ranking", methods=["GET"])
def ranking():
    """Produce a ranking for current session

    @return:    ranking result (dict)
                header contains meta-data
                body contains ranked document list
    """

    # look for "mandatory" GET-parameters (query, container_name, session_id)
    query = request.args.get("query", None)
    container_name = request.args.get("container", None)
    session_id = request.args.get("sid", None)

    # Look for optional GET-parameters and set default values
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    # Cached results for known (session ID, query) combinations
    if session_id and query:
        ranking = (
            db.session.query(Result)
            .filter_by(session_id=session_id, q=query, page=page, rpp=rpp)
            .first()
        )
        if ranking:
            if ranking.tdi:
                ranking = db.session.query(Result).filter_by(id=ranking.tdi).first()

            system_id = (
                db.session.query(Session)
                .filter_by(id=session_id)
                .first()
                .system_ranking
            )
            container_name = (
                db.session.query(System).filter_by(id=system_id).first().name
            )
            response = build_response(ranking, container_name)
            return jsonify(response)

    # If no query is given, return an empty response
    # TODO: Is this save?
    if query is None:
        return create_dict_response(status=1, ts=round(time.time() * 1000))

    # Select least served container if no container_name is given. This is the default case for an interleaved experiment.
    if container_name is None:
        # Depricated precomputed runs code. Will be removed in the future.
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

    # Create new session if no session_id is given
    if session_id is None:
        session_id = create_new_session(container_name, type="ranker")
    else:
        # SessionID is given, but does not exist in the database
        if db.session.query(Session).filter_by(id=session_id) is None:
            session_id = create_new_session(
                container_name=container_name, sid=session_id, type="ranker"
            )

        # TODO: At this point, the containername is given! The container name is overwritten here. Therefore I commented out the following lines.
        # ranking_system_id = (
        #     db.session.query(Session).filter_by(id=session_id).first().system_ranking
        # )
        # container_name = db.session.query(System).filter_by(id=ranking_system_id).first().name

    # Query the experimental and baseline system
    ranking, result = query_system(
        container_name, query, rpp, page, session_id, type="EXP"
    )

    if current_app.config["INTERLEAVE"]:
        current_app.logger.info("Interleaving rankings")
        ranking_base, result_base = query_system(
            current_app.config["RANKING_BASELINE_CONTAINER"],
            query,
            rpp,
            page,
            session_id,
            type="BASE",
        )

        interleaved_ranking = interleave_rankings(ranking, ranking_base)

        response = build_response(
            ranking,
            container_name,
            interleaved_ranking,
            ranking_base,
            current_app.config["RANKING_BASELINE_CONTAINER"],
            result,
            result_base,
        )

    else:
        response = build_response(ranking, container_name, result=result)

    return jsonify(response)
