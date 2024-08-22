import docker
import json
import time
from datetime import datetime
import requests
from flask import jsonify, request, current_app
from app import api
from app.models import db, Session, System, Result, Feedback
from app.services.interleave_service import tdi
from app.utils import create_dict_response
from pytz import timezone
from . import api
from app.services.session_service import create_new_session

client = docker.DockerClient(base_url="unix://var/run/docker.sock")
tz = timezone("Europe/Berlin")


def single_ranking(ranking):
    """
    Add ranking to database

    @param ranking: a ranking of type Result

    @return
        ranked items (dict)

    """
    db.session.add(ranking)
    db.session.commit()

    return ranking.items


def interleave(ranking_exp, ranking_base):
    """
    Create interleaved ranking from experimental and baseline system
    Used method: Team-Draft-Interleaving (TDI) [1]

    [1] "How Does Clickthrough Data Reflect Retrieval Quality?"
        Radlinski, Kurup, Joachims
        Published in CIKM '15 2015

    @param ranking_exp:     experimental ranking (Result)
    @param ranking_base:    baseline ranking (Result)
    @return:                interleaved ranking (dict)
    """
    base = {k: v.get("docid") for k, v in ranking_base.items.items()}
    exp = {k: v.get("docid") for k, v in ranking_exp.items.items()}

    item_dict = tdi(base, exp)
    ranking = Result(
        session_id=ranking_exp.session_id,
        system_id=ranking_exp.system_id,
        type="RANK",
        q=ranking_exp.q,
        q_date=ranking_exp.q_date,
        q_time=ranking_exp.q_time,
        num_found=ranking_exp.num_found,
        hits=ranking_base.num_found,
        page=ranking_exp.page,
        rpp=ranking_exp.rpp,
        items=item_dict,
    )

    db.session.add(ranking)
    db.session.commit()

    ranking_id = ranking.id
    ranking.tdi = ranking_id

    ranking_exp.tdi = ranking_id
    db.session.add(ranking_exp)
    db.session.commit()

    ranking_base.tdi = ranking_id
    db.session.add(ranking_base)
    db.session.commit()

    return ranking.items


def rest(container_name, query, rpp, page):
    """
    Produce container-ranking via rest-call implementation

    @param container_name:  container name (str)
    @param query:           search query (str)
    @param rpp:             results per page (int)
    @param page:            page number (int)

    @return:                container-ranking (dict)
    """
    if current_app.config["DEBUG"]:
        container = client.containers.get(container_name)
        ip_address = container.attrs["NetworkSettings"]["Networks"][
            "stella-app_default"
        ]["IPAddress"]
        content = requests.get(
            "http://" + ip_address + ":5000/ranking",
            params={"query": query, "rpp": rpp, "page": page},
        ).content
        return json.loads(content)

    content = requests.get(
        f"http://{container_name}:5000/ranking",
        params={"query": query, "rpp": rpp, "page": page},
    ).content
    return json.loads(content)


def cmd(container_name, query, rpp, page):
    """
    Produce container-ranking via classical cmd-call (fallback solution, much slower than rest-implementation)

    @param container_name:  container name (str)
    @param query:           search query (str)
    @param rpp:             results per page (int)
    @param page:            page number (int)

    @return:                container-ranking (dict)
    """
    container = client.containers.get(container_name)
    cmd = "python3 /script/ranking {} {} {}".format(query, rpp, page)
    exec_res = container.exec_run(cmd)
    result = json.loads(exec_res.output.decode("utf-8"))
    return result


def query_system(container_name, query, rpp, page, session_id, type="EXP"):
    """
    Produce ranking from dockerized system

    @param container_name:  container name (str)
    @param query:           search query (str)
    @param rpp:             results per page (int)
    @param page:            page number (int)
    @param session_id:      session_id (int)
    @param type:            ranking type (str 'EXP' or 'BASE')

    @return:                ranking (Result)
    """
    current_app.logger.debug(f'produce ranking with container: "{container_name}"...')

    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)

    ts_start = time.time()
    ts = round(ts_start * 1000)

    # increase counter before actual request, in case of a failure
    system = System.query.filter_by(name=container_name).first()
    if query in current_app.config["HEAD_QUERIES"]:
        system.num_requests += 1
    else:
        system.num_requests_no_head += 1
    db.session.commit()

    if current_app.config["REST_QUERY"]:
        result = rest(container_name, query, rpp, page)
    else:
        result = cmd(container_name, query, rpp, page)

    ts_end = time.time()
    # calc query execution time in ms
    q_time = round((ts_end - ts_start) * 1000)

    item_dict = {
        i + 1: {"docid": result["itemlist"][i], "type": type}
        for i in range(0, len(result["itemlist"]))
    }

    ranking = Result(
        session_id=session_id,
        system_id=System.query.filter_by(name=container_name).first().id,
        type="RANK",
        q=query,
        q_date=q_date,
        q_time=q_time,
        num_found=result["num_found"],
        page=page,
        rpp=rpp,
        items=item_dict,
    )

    # system = System.query.filter_by(name=container_name).first()
    # system.num_requests += 1
    db.session.add(ranking)
    db.session.commit()

    return ranking


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
    rpp = request.args.get("rpp", default=20, type=int)

    # Return cached results for known (session ID, query) combinations
    # tested: true
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

            response = {
                "header": {
                    "sid": ranking.session_id,
                    "rid": ranking.id,
                    "q": query,
                    "page": ranking.page,
                    "rpp": ranking.rpp,
                    "hits": ranking.hits,
                    "container": {"exp": container_name},
                },
                "body": ranking.items,
            }
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
        # make new session and get session_id as sid
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
    ranking_exp = query_system(container_name, query, rpp, page, session_id)

    ranking_base = query_system(
        current_app.config["RANKING_BASELINE_CONTAINER"],
        query,
        rpp,
        page,
        session_id,
        type="BASE",
    )

    if current_app.config["INTERLEAVE"]:
        response = interleave(ranking_exp, ranking_base)
        response_complete = {
            "header": {
                "sid": ranking_exp.session_id,
                "rid": ranking_exp.tdi,
                "q": query,
                "page": page,
                "rpp": rpp,
                "hits": ranking_base.num_found,
                "container": {
                    "base": current_app.config["RANKING_BASELINE_CONTAINER"],
                    "exp": container_name,
                },
            },
            "body": response,
        }
    else:
        response = single_ranking(ranking_exp)
        response_complete = {
            "header": {
                "sid": ranking_exp.session_id,
                "rid": ranking_exp.id,
                "q": query,
                "page": page,
                "rpp": rpp,
                "hits": ranking_exp.num_found,
                "container": {"exp": container_name},
            },
            "body": response,
        }

    return jsonify(response_complete)
