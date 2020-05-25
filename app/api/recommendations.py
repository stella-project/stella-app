import docker
import logging
import json
import time
from datetime import datetime
import requests
from flask import jsonify, request
from . import api
from core import get_least_served
from core.models import db, System, Session, Result, Feedback
from config import conf
from utils import create_dict_response
from core.interleave import tdi, tdi_rec

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def new_session(container_name, container_rec_name):
    session = Session(start=datetime.now(),
                      system_ranking=System.query.filter_by(name=container_name).first().id,
                      system_recommendation=System.query.filter_by(name=container_rec_name).first().id,
                      site_user='unknown',
                      exit=False,
                      sent=False)
    db.session.add(session)
    db.session.commit()

    return session.id


def rest_rec_data(container_name, item_id, rpp, page):
    if conf['app']['DEBUG']:
        container = client.containers.get(container_name)
        ip_address = container.attrs['NetworkSettings']['Networks']['stella-app_default']['IPAddress']
        content = requests.get('http://' + ip_address + ':5000/recommendation/datasets', params={'item_id': item_id, 'rpp': rpp, 'page': page}).content
        return json.loads(content)

    content = requests.get(f'http://{container_name}:5000/recommendation/datasets', params={'item_id': item_id, 'rpp': rpp, 'page': page}).content
    return json.loads(content)
    pass


def cmd_rec_data(container_name, query, rpp, page):
    pass


def rest_rec_pub(container_name, item_id, rpp, page):
    if conf['app']['DEBUG']:
        container = client.containers.get(container_name)
        ip_address = container.attrs['NetworkSettings']['Networks']['stella-app_default']['IPAddress']
        content = requests.get('http://' + ip_address + ':5000/recommendation/publications',
                               params={'item_id': item_id, 'rpp': rpp, 'page': page}).content
        return json.loads(content)

    content = requests.get(f'http://{container_name}:5000/recommendation/publications',
                           params={'item_id': item_id, 'rpp': rpp, 'page': page}).content
    return json.loads(content)
    pass


def cmd_rec_pub():
    pass


def query_system(container_name, item_id, rpp, page, session_id, logger, type='EXP', rec_type='DATA'):
    logger.debug(f'produce recommendation with container: "{container_name}"...')
    q_date = datetime.now().replace(microsecond=0)
    ts_start = time.time()
    ts = round(ts_start*1000)

    if conf['app']['REST_QUERY']:
        if rec_type == 'DATA':
            result = rest_rec_data(container_name, item_id, rpp, page)
        if rec_type == 'PUB':
            result = rest_rec_pub(container_name, item_id, rpp, page)
    else:
        if rec_type == 'DATA':
            result = cmd_rec_data(container_name, item_id, rpp, page)
        if rec_type == 'PUB':
            result = cmd_rec_pub(container_name, item_id, rpp, page)

    ts_end = time.time()
    # calc query execution time in ms
    q_time = round((ts_end-ts_start)*1000)
    item_dict = {i: {'docid': result['itemlist'][i], 'type': type} for i in range(1, len(result['itemlist']))}

    recommendation = Result(session_id=session_id,
                            system_id=System.query.filter_by(name=container_name).first().id,
                            type='REC_' + rec_type,
                            q=item_id,
                            q_date=q_date,
                            q_time=q_time,
                            num_found=result['num_found'],
                            page=page,
                            rpp=rpp,
                            items=item_dict)

    system = System.query.filter_by(name=container_name).first()
    system.num_requests += 1
    db.session.add(recommendation)
    db.session.commit()

    return recommendation


def interleave(recommendation_exp, recommendation_base, rec_type='DATA'):
    base = {k: v.get('docid') for k, v in recommendation_base.items.items()}
    exp = {k: v.get('docid') for k, v in recommendation_exp.items.items()}

    if rec_type == 'DATA':
        item_dict = tdi_rec(base, exp)
    if rec_type == 'PUB':
        item_dict = tdi(base, exp)
    recommendation = Result(session_id=recommendation_exp.session_id,
                            system_id=recommendation_exp.system_id,
                            type='REC_' + rec_type,
                            q=recommendation_exp.q,
                            q_date=recommendation_exp.q_date,
                            q_time=recommendation_exp.q_time,
                            num_found=recommendation_exp.num_found,
                            page=recommendation_exp.page,
                            rpp=recommendation_exp.rpp,
                            items=item_dict)

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
    db.session.add(recommendation)
    db.session.commit()

    return recommendation.items


@api.route('/recommendation/<int:id>/feedback', methods=['POST'])
def post_rec_feedback(id):
    clicks = request.values.get('clicks', None)
    if clicks is not None:
        recommendation = Result.query.get_or_404(id)
        feedback = Feedback(start=recommendation.q_date,
                            session_id=recommendation.session_id,
                            interleave=recommendation.tdi is not None,
                            clicks=clicks)

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

        return {"msg": "Added new feedback with success!"}, 201


@api.route("/recommendation/datasets", methods=["GET"])
def recommend_dataset():
    logger = logging.getLogger("stella-app")
    # look for mandatory GET-parameters (query, container_name)
    item_id = request.args.get('item_id', None)
    container_name = request.args.get('container', None)
    session_id = request.args.get('sid', None)

    # Look for optional GET-parameters and set default values
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=10, type=int)

    # no item_id ? -> Nothing to do
    if item_id is None:
        return create_dict_response(status=1,
                                    ts=round(time.time()*1000))

    # no container_name specified? -> select least served container
    if container_name is None:
        # container_name = get_least_served(conf["app"]["container_dict"])
        container_name = System.query.filter(System.name != conf['app']['container_recommendation_baseline']).filter(System.name.notin_(conf["app"]["container_list"])).order_by(System.num_requests).first().name
        container_rank_name = System.query.filter(System.name != conf['app']['container_recommendation_baseline']).filter(System.name.notin_(conf["app"]["container_list_recommendation"])).order_by(System.num_requests).first().name

    if session_id is None:
        # make new session and get session_id as sid
        session_id = new_session(container_rank_name, container_name)
    else:
        recommendation_id = Session.query.get_or_404(session_id).system_recommendation
        container_name = System.query.filter_by(id=recommendation_id).first().name

    recommendation_exp = query_system(container_name, item_id, rpp, page, session_id, logger)

    if conf['app']['INTERLEAVE']:
        recommendation_base = query_system(conf['app']['container_recommendation_baseline'], item_id, rpp, page, session_id, logger, type='BASE')
        response = interleave(recommendation_exp, recommendation_base)
    else:
        response = single_recommendation(recommendation_exp)

    return jsonify(response)


@api.route("/recommendation/publications", methods=["GET"])
def recommend():
    logger = logging.getLogger("stella-app")
    # look for mandatory GET-parameters (query, container_name)
    item_id = request.args.get('item_id', None)
    container_name = request.args.get('container', None)
    session_id = request.args.get('sid', None)

    # Look for optional GET-parameters and set default values
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=10, type=int)

    # no item_id ? -> Nothing to do
    if item_id is None:
        return create_dict_response(status=1,
                                    ts=round(time.time()*1000))

    # no container_name specified? -> select least served container
    if container_name is None:
        # container_name = get_least_served(conf["app"]["container_dict"])
        container_name = System.query.filter(System.name != conf['app']['container_recommendation_baseline']).filter(System.name.notin_(conf["app"]["container_list"])).order_by(System.num_requests).first().name
        container_rank_name = System.query.filter(System.name != conf['app']['container_recommendation_baseline']).filter(System.name.notin_(conf["app"]["container_list_recommendation"])).order_by(System.num_requests).first().name

    if session_id is None:
        # make new session and get session_id as sid
        session_id = new_session(container_rank_name, container_name)
    else:
        recommendation_id = Session.query.get_or_404(session_id).system_recommendation
        container_name = System.query.filter_by(id=recommendation_id).first().name

    recommendation_exp = query_system(container_name, item_id, rpp, page, session_id, logger, rec_type='PUB')

    if conf['app']['INTERLEAVE']:
        recommendation_base = query_system(conf['app']['container_recommendation_baseline'], item_id, rpp, page, session_id, logger, type='BASE', rec_type='PUB')
        response = interleave(recommendation_exp, recommendation_base, rec_type='PUB')
    else:
        response = single_recommendation(recommendation_exp)

    return jsonify(response)
