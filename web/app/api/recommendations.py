import json
import time
from datetime import datetime
from uuid import uuid4
from . import api

import docker
import requests
from app.models import Feedback, Result, Session, System, db
from app.services.interleave_service import tdi
from app.utils import create_dict_response
from flask import current_app, jsonify, request
from pytz import timezone

from app.services.session_service import create_new_session


tz = timezone("Europe/Berlin")

import os
# import os
if os.name == 'nt':  # Windows
    client = docker.DockerClient(base_url="npipe:////./pipe/docker_engine")
else:  # Unix-based systems like Linux or macOS
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")




def rest_rec_data(container_name, item_id, rpp, page):
    """
    get the container_name, item_id , rpp and page number and return a ranking datasets produced by container_name
    Args:
        container_name: name of container to produce recommendation
        item_id: item_id as seed for recommendation
        rpp: rank par page
        page: page number

    Returns:
        dataset recommendation ranking for item_id
    """
    if current_app.config["DEBUG"]:
        container = client.containers.get(container_name)
        ip_address = container.attrs["NetworkSettings"]["Networks"][
            "stella-app_default"
        ]["IPAddress"]
        content = requests.get(
            "http://" + ip_address + ":5000/recommendation/datasets",
            params={"item_id": item_id, "rpp": rpp, "page": page},
        ).content
        return json.loads(content)

    content = requests.get(
        f"http://{container_name}:5000/recommendation/datasets",
        params={"item_id": item_id, "rpp": rpp, "page": page},
    ).content
    return json.loads(content)


def cmd_rec_data(container_name, query, rpp, page):
    pass


def rest_rec_pub(container_name, item_id, rpp, page):
    """
    get the container_name, item_id , rpp and page number and return a ranking publications produced by container_name
    Args:
        container_name: name of container to produce recommendation
        item_id: item_id as seed for recommendation
        rpp: rank par page
        page: page number

    Returns:
        publications recommendation ranking for item_id
    """
    if current_app.config["DEBUG"]:
        container = client.containers.get(container_name)
        ip_address = container.attrs["NetworkSettings"]["Networks"][
            "stella-app_default"
        ]["IPAddress"]
        content = requests.get(
            "http://" + ip_address + ":5000/recommendation/publications",
            params={"item_id": item_id, "rpp": rpp, "page": page},
        ).content
        return json.loads(content)

    content = requests.get(
        f"http://{container_name}:5000/recommendation/publications",
        params={"item_id": item_id, "rpp": rpp, "page": page},
    ).content
    return json.loads(content)


def cmd_rec_pub():
    pass


def query_system(
    container_name, item_id, rpp, page, session_id, type="EXP", rec_type="DATA"
):
    """

    Args:
        container_name: container_name set to produce the recommendation
        item_id: id of seed item for recommendation
        rpp: ranking per page
        page: page number
        session_id: session id
        type: type of container
        rec_type: type pf recommended items

    Returns:
        for session_id returns recommendation result of rec_type
    """
    current_app.logger.debug(
        f'produce recommendation with container: "{container_name}"...'
    )
    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()
    ts = round(ts_start * 1000)

    # increase counter before actual request, in case of a failure
    system = System.query.filter_by(name=container_name).first()
    if item_id in current_app.config["HEAD_ITEMS"]:
        system.num_requests += 1
    else:
        system.num_requests_no_head += 1
    db.session.commit()

    if current_app.config["REST_QUERY"]:
        if rec_type == "DATA":
            result = rest_rec_data(container_name, item_id, rpp, page)
        if rec_type == "PUB":
            result = rest_rec_pub(container_name, item_id, rpp, page)
    else:
        if rec_type == "DATA":
            result = cmd_rec_data(container_name, item_id, rpp, page)
        if rec_type == "PUB":
            result = cmd_rec_pub(container_name, item_id, rpp, page)

    ts_end = time.time()
    # calc query execution time in ms
    q_time = round((ts_end - ts_start) * 1000)
    item_dict = {
        i + 1: {"docid": result["itemlist"][i], "type": type}
        for i in range(0, len(result["itemlist"]))
    }

    recommendation = Result(
        session_id=session_id,
        system_id=System.query.filter_by(name=container_name).first().id,
        type="REC_" + rec_type,
        q=item_id,
        q_date=q_date,
        q_time=q_time,
        num_found=result["num_found"],
        page=page,
        rpp=rpp,
        items=item_dict,
    )

    # system = System.query.filter_by(name=container_name).first()
    # system.num_requests += 1
    db.session.add(recommendation)
    db.session.commit()

    return recommendation


def interleave(recommendation_exp, recommendation_base, rec_type="DATA"):
    """
    interleave the experimental with base ranking for recommending item types rec_type
    Args:
        recommendation_exp: ranking of experimental system
        recommendation_base: ranking of base system
        rec_type: type of recommended items

    Returns:
        a list of items produced experimental system interleaved with base ranking
    """
    base = {k: v.get("docid") for k, v in recommendation_base.items.items()}
    exp = {k: v.get("docid") for k, v in recommendation_exp.items.items()}

    if rec_type == "DATA":
        item_dict = tdi(base, exp)
    if rec_type == "PUB":
        item_dict = tdi(base, exp)
    recommendation = Result(
        session_id=recommendation_exp.session_id,
        system_id=recommendation_exp.system_id,
        type="REC_" + rec_type,
        q=recommendation_exp.q,
        q_date=recommendation_exp.q_date,
        q_time=recommendation_exp.q_time,
        num_found=recommendation_exp.num_found,
        hits=recommendation_base.num_found,
        page=recommendation_exp.page,
        rpp=recommendation_exp.rpp,
        items=item_dict,
    )

    db.session.add(recommendation)
    db.session.commit()

    recommendation_id = recommendation.id
    recommendation.tdi = recommendation_id

    recommendation_base.tdi = recommendation_id
    db.session.add(recommendation_base)
    db.session.commit()

    recommendation_exp.tdi = recommendation_id
    db.session.add(recommendation_exp)
    db.session.commit()

    return recommendation.items


def single_recommendation(recommendation):
    """

    Args:
        recommendation:

    Returns:

    """
    db.session.add(recommendation)
    db.session.commit()

    return recommendation.items


@api.route("/recommendation/<int:id>/feedback", methods=["POST"])
def post_rec_feedback(id):
    """
    post feedback of ranking for recommendation with identifier id
    Args:
        id: identifier of ranking for recommendation

    Returns:
        post message
    """
    clicks = request.values.get("clicks", None)
    if clicks is None:
        clicks = request.json.get("clicks", None)

    if clicks is not None:
        recommendation = Result.query.get_or_404(id)
        feedback = Feedback(
            start=recommendation.q_date,
            session_id=recommendation.session_id,
            interleave=recommendation.tdi is not None,
            clicks=clicks,
        )

        db.session.add(feedback)
        db.session.commit()
        recommendation.feedback_id = feedback.id
        db.session.add(recommendation)
        db.session.commit()
        recommendations = Result.query.filter_by(tdi=recommendation.id).all()
        for r in recommendations:
            r.feedback_id = feedback.id
        db.session.add_all(recommendations)
        db.session.commit()

        return jsonify({"msg": "Added new feedback with success!"}), 201


@api.route("/recommendation/datasets/<int:rid>", methods=["GET"])
def recommend_dataset_from_db(rid):
    recommendation = Result.query.get_or_404(rid)
    return jsonify(recommendation.serialize)


@api.route("/recommendation/datasets", methods=["GET"])
def recommend_dataset():
    """
    Returns:
        ranked list for recommending dataset for itemid
    """

    # look for mandatory GET-parameters (query, container_name)
    itemid = request.args.get("itemid", None)
    container_name = request.args.get("container", None)
    session_id = request.args.get("sid", None)

    # if recommendations have been retrieved for a specific item before in the corresponding session, read it from the database
    if session_id and itemid:
        recommendation = Result.query.filter_by(session_id=session_id, q=itemid).first()
        if recommendation:
            if recommendation.tdi:
                recommendation = Result.query.filter_by(id=recommendation.tdi).first()

            system_id = (
                Session.query.filter_by(id=session_id).first().system_recommendation
            )
            container_name = System.query.filter_by(id=system_id).first().name

            response = {
                "header": {
                    "sid": recommendation.session_id,
                    "rid": recommendation.id,
                    "itemid": itemid,
                    "page": recommendation.page,
                    "rpp": recommendation.rpp,
                    "hits": recommendation.hits,
                    "type": "DATA",
                    "container": {"exp": container_name},
                },
                "body": recommendation.items,
            }
            return jsonify(response)

    # Look for optional GET-parameters and set default values
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    # no item_id ? -> Nothing to do
    if itemid is None:
        return create_dict_response(status=1, ts=round(time.time() * 1000))

    # no container_name specified? -> select least served container
    if container_name is None:

        if itemid in current_app.config["HEAD_ITEMS"]:
            # container_name = get_least_served(current_app.config["container_dict"])
            container_name = (
                System.query.filter(
                    System.name != current_app.config["RECOMMENDER_BASELINE_CONTAINER"]
                )
                .filter(
                    System.name.notin_(
                        current_app.config["RANKING_CONTAINER_NAMES"]
                        + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
                    )
                )
                .order_by(System.num_requests)
                .first()
                .name
            )

            # The following code is not required since we do not have any use case for sessions with rankings and recommendations right now.
            # container_rank = System.query.filter(System.name != conf['app']['container_recommendation_baseline']).filter(System.name.notin_(current_app.config["container_list_recommendation"])).order_by(System.num_requests).first()
            # if container_rank is not None:
            #     container_rank_name = container_rank.name
            # else:
            #     container_rank_name = None

        else:
            container_name = (
                db.session.query(System)
                .filter(
                    System.name != current_app.config["RECOMMENDER_BASELINE_CONTAINER"]
                )
                .filter(
                    System.name.notin_(
                        current_app.config["RANKING_CONTAINER_NAMES"]
                        + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
                        + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
                    )
                )
                .order_by(System.num_requests_no_head)
                .first()
                .name
            )

    try:
        if session_id is None:
            # make new session and get session_id as sid
            session_id = create_new_session(
                container_name=container_name, type="recommender"
            )
        else:
            if db.session.query(Session).get(session_id) is None:
                session_id = create_new_session(
                    container_name=container_name, sid=session_id, type="recommender"
                )

            recommendation_id = Session.query.get_or_404(
                session_id
            ).system_recommendation
            container_name = (
                db.session.query(System).filter_by(id=recommendation_id).first().name
            )

        recommendation_exp = query_system(container_name, itemid, rpp, page, session_id)

        if current_app.config["INTERLEAVE"]:
            recommendation_base = query_system(
                current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
                itemid,
                rpp,
                page,
                session_id,
                type="BASE",
            )
            response = interleave(recommendation_exp, recommendation_base)

            response_complete = {
                "header": {
                    "sid": recommendation_exp.session_id,
                    "rid": recommendation_exp.tdi,
                    "itemid": itemid,
                    "page": page,
                    "rpp": rpp,
                    "hits": recommendation_base.num_found,
                    "type": "DATA",
                    "container": {
                        "base": current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
                        "exp": container_name,
                    },
                },
                "body": response,
            }
        else:
            response = single_recommendation(recommendation_exp)

            response_complete = {
                "header": {
                    "sid": recommendation_exp.session_id,
                    "rid": recommendation_exp.id,
                    "itemid": itemid,
                    "page": page,
                    "rpp": rpp,
                    "hits": recommendation_exp.num_found,
                    "type": "DATA",
                    "container": {"exp": container_name},
                },
                "body": response,
            }

        # response_complete = {'header': {'session': recommendation_exp.session_id,
        #                                 'recommendation': recommendation_exp.id},
        #                      'body': response}

        # return jsonify(response)
        return jsonify(response_complete)

    except Exception as e:
        print(e)
        return create_dict_response(status=1, ts=round(time.time() * 1000))


@api.route("/recommendation/publications/<int:rid>", methods=["GET"])
def recommend_from_db(rid):
    recommendation = Result.query.get_or_404(rid)
    return jsonify(recommendation.serialize)


@api.route("/recommendation/publications", methods=["GET"])
def recommend():
    """

    Returns:
        ranked list for recommending publications for itemid
    """
    # look for mandatory GET-parameters (query, container_name)
    itemid = request.args.get("itemid", None)
    container_name = request.args.get("container", None)
    session_id = request.args.get("sid", None)

    # if recommendations have been retrieved for a specific item before in the corresponding session, read it from the database
    if session_id and itemid:
        recommendation = Result.query.filter_by(session_id=session_id, q=itemid).first()
        if recommendation:
            if recommendation.tdi:
                recommendation = Result.query.filter_by(id=recommendation.tdi).first()

            system_id = (
                Session.query.filter_by(id=session_id).first().system_recommendation
            )
            container_name = System.query.filter_by(id=system_id).first().name

            response = {
                "header": {
                    "sid": recommendation.session_id,
                    "rid": recommendation.id,
                    "itemid": itemid,
                    "page": recommendation.page,
                    "rpp": recommendation.rpp,
                    "type": "PUB",
                    "container": {"exp": container_name},
                },
                "body": recommendation.items,
            }
            return jsonify(response)

    # Look for optional GET-parameters and set default values
    page = request.args.get("page", default=0, type=int)
    rpp = request.args.get("rpp", default=10, type=int)

    # no item_id ? -> Nothing to do
    if itemid is None:
        return create_dict_response(status=1, ts=round(time.time() * 1000))

    # no container_name specified? -> select least served container
    if container_name is None:
        if itemid in current_app.config["HEAD_ITEMS"]:
            container_name = (
                System.query.filter(
                    System.name != current_app.config["RECOMMENDER_BASELINE_CONTAINER"]
                )
                .filter(
                    System.name.notin_(current_app.config["RANKING_CONTAINER_NAMES"])
                    + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
                )
                .order_by(System.num_requests)
                .first()
                .name
            )
        else:
            container_name = (
                System.query.filter(
                    System.name != current_app.config["RECOMMENDER_BASELINE_CONTAINER"]
                )
                .filter(
                    System.name.notin_(
                        current_app.config["RANKING_CONTAINER_NAMES"]
                        + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
                        + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
                    )
                )
                .order_by(System.num_requests)
                .first()
                .name
            )

            # We don't have any use case for sessions with rankings and recommendations right now.
            # container_rank_name = System.query.filter(System.name != conf['app']['container_recommendation_baseline']).filter(System.name.notin_(current_app.config["container_list_recommendation"])).order_by(System.num_requests).first().name

    if session_id is None:
        # make new session and get session_id as sid
        session_id = create_new_session(container_name=container_name, type="recommender")
    else:
        if db.session.query(Session).get(session_id) is None:
            session_id = create_new_session(
                container_name=container_name, sid=session_id, type="recommender"
            )

        recommendation_id = Session.query.get_or_404(session_id).system_recommendation
        container_name = System.query.filter_by(id=recommendation_id).first().name

    recommendation_exp = query_system(
        container_name, itemid, rpp, page, session_id, rec_type="PUB"
    )

    if current_app.config["INTERLEAVE"]:
        recommendation_base = query_system(
            current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
            itemid,
            rpp,
            page,
            session_id,
            type="BASE",
            rec_type="PUB",
        )
        response = interleave(recommendation_exp, recommendation_base, rec_type="PUB")

        response_complete = {
            "header": {
                "sid": recommendation_exp.session_id,
                "rid": recommendation_exp.tdi,
                "itemid": itemid,
                "page": page,
                "rpp": rpp,
                "type": "PUB",
                "container": {
                    "base": current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
                    "exp": container_name,
                },
            },
            "body": response,
        }
    else:
        response = single_recommendation(recommendation_exp)
        # response_complete = {'header': {'session': recommendation_exp.session_id,
        #                                 'recommendation': recommendation_exp.id},
        #                      'body': response}
        response_complete = {
            "header": {
                "sid": recommendation_exp.session_id,
                "rid": recommendation_exp.id,
                "itemid": itemid,
                "page": page,
                "rpp": rpp,
                "type": "PUB",
                "container": {"exp": container_name},
            },
            "body": response,
        }

    # return jsonify(response)
    return jsonify(response_complete)
