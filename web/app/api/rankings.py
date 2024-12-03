import docker
from app.models import Feedback, Result, Session, db
from app.services.ranking_service import make_ranking
from app.services.session_service import create_new_session
from app.services.system_service import get_least_served_system
from app.services.profile_service import profile_route
from flask import jsonify, request, current_app
from pytz import timezone
import asyncio

from . import api

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
@profile_route
def ranking():
    """Produce a ranking for current session

    @return:    ranking result (dict)
                header contains meta-data
                body contains ranked document list
    """
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    query = request.args.get("query", None)
    if query is None:
        return "Missing query string", 400

    container_name = request.args.get("container", None)
    if container_name is None:
        container_name = get_least_served_system(query)

    session_id = request.args.get("sid", None)
    if session_id is None or db.session.query(Session).filter_by(id=session_id) is None:
        session_id = create_new_session(container_name, type="ranker")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(
        make_ranking(container_name, query, rpp, page, session_id)
    )

    return response
