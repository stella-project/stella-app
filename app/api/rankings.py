import docker
import logging
import json
import time
from datetime import datetime
import requests
import random
from flask import jsonify, request
from . import api
from core import get_least_served
from core.models import db, Session, System, Result, Feedback
from core.interleave import tdi
from config import conf
from utils import create_dict_response

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def single_ranking(ranking):
    db.session.add(ranking)
    db.session.commit()

    return ranking.items


def interleave(ranking_exp, ranking_base):
    base = {k: v.get('docid') for k, v in ranking_base.items.items()}
    exp = {k: v.get('docid') for k, v in ranking_exp.items.items()}

    item_dict = tdi(base, exp)
    ranking = Result(session_id=ranking_exp.session_id,
                     system_id=ranking_exp.system_id,
                     type='RANK',
                     q=ranking_exp.q,
                     q_date=ranking_exp.q_date,
                     q_time=ranking_exp.q_time,
                     num_found=ranking_exp.num_found,
                     page=ranking_exp.page,
                     rpp=ranking_exp.rpp,
                     items=item_dict)

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
    if conf['app']['DEBUG']:
        container = client.containers.get(container_name)
        ip_address = container.attrs['NetworkSettings']['Networks']['stella-app_default']['IPAddress']
        content = requests.get('http://' + ip_address + ':5000/ranking', params={'query': query, 'rpp': rpp, 'page': page}).content
        return json.loads(content)

    content = requests.get(f'http://{container_name}:5000/ranking', params={'query': query, 'rpp': rpp, 'page': page}).content
    return json.loads(content)


def cmd(container_name, query, rpp, page):
    container = client.containers.get(container_name)
    cmd = 'python3 /script/ranking {} {} {}'.format(query, rpp, page)
    exec_res = container.exec_run(cmd)
    result = json.loads(exec_res.output.decode('utf-8'))
    return result


def query_system(container_name, query, rpp, page, session_id, logger, type='EXP'):

    logger.debug(f'produce ranking with container: "{container_name}"...')

    q_date = datetime.now().replace(microsecond=0)

    ts_start = time.time()
    ts = round(ts_start*1000)

    if conf['app']['REST_QUERY']:
        result = rest(container_name, query, rpp, page)
    else:
        result = cmd(container_name, query, rpp, page)

    ts_end = time.time()
    # calc query execution time in ms
    q_time = round((ts_end-ts_start)*1000)

    item_dict = {i: {'docid': result['itemlist'][i], 'type': type} for i in range(1, len(result['itemlist']))}

    ranking = Result(session_id=session_id,
                     system_id=System.query.filter_by(name=container_name).first().id,
                     type='RANK',
                     q=query,
                     q_date=q_date,
                     q_time=q_time,
                     num_found=result['num_found'],
                     page=page,
                     rpp=rpp,
                     items=item_dict)

    system = System.query.filter_by(name=container_name).first()
    system.num_requests += 1
    db.session.commit()

    return ranking


def new_session(container_name):
    session = Session(start=datetime.now(),
                      system_ranking=System.query.filter_by(name=container_name).first().id,
                      exit=False,
                      sent=False)
    db.session.add(session)
    db.session.commit()

    return session.id


@api.route("/test/<string:container_name>", methods=["GET"])
def test(container_name):
    ''' run test script for given container name'''
    if request.method == 'GET':
        container = client.containers.get(container_name)

        cmd = 'python3 /script/test'

        out = container.exec_run(cmd)

        return "<h1> " + out.output.decode("utf-8") + " </h1>"


@api.route('/ranking/<int:id>/feedback', methods=['POST'])
def post_feedback(id):
    # 1) check if ranking with id exists
    # 2) check if feedback is not already in db
    clicks = request.values.get('clicks', None)
    if clicks is not None:
        ranking = Result.query.get_or_404(id)
        feedback = Feedback(start=ranking.q_date,
                            session_id=ranking.session_id,
                            interleave=ranking.tdi is not None,
                            clicks=clicks)

        db.session.add(feedback)
        db.session.commit()
        ranking.feedback_id = feedback.id
        db.session.add(ranking)
        db.session.commit()
        rankings = Result.query.filter_by(tdi=ranking.id).all()
        for r in rankings:
            r.feedback_id = feedback.id
        db.session.add_all(rankings)
        db.session.commit()

        return {"msg": "Added new feedback with success!"}, 201


@api.route("/ranking", methods=["GET"])
def ranking():
    logger = logging.getLogger("stella-app")
    # look for mandatory GET-parameters (query, container_name)
    query = request.args.get('query', None)
    container_name = request.args.get('container', None)
    session_id = request.args.get('sid', None)

    # Look for optional GET-parameters and set default values
    page = request.args.get('page', default=0, type=int)
    rpp = request.args.get('rpp', default=20, type=int)

    # no query ? -> Nothing to do
    if query is None:
        return create_dict_response(status=1,
                                    ts=round(time.time()*1000))
    
    # no container_name specified? -> select least served container
    if container_name is None:
        # container_name = get_least_served(conf["app"]["container_dict"])
        container_name = System.query.filter(System.name != conf['app']['container_baseline']).filter(System.name.notin_(conf["app"]["container_list_recommendation"])).order_by(System.num_requests).first().name

    # container_name does not exist in config? -> Nothing to do
    # i think this check is not necessary anymore. the system names in the database are extracted from
    # the config file when the application starts
    if not container_name in conf["app"]["container_dict"]:
        return create_dict_response(status=1,
                                    ts=round(time.time()*1000))

    if session_id is None:
        # make new session and get session_id as sid
        session_id = new_session(container_name)
    else:
        ranking_id = Session.query.get_or_404(session_id).system_ranking
        container_name = System.query.filter_by(id=ranking_id).first().name

    ranking_exp = query_system(container_name, query, rpp, page, session_id, logger)

    if conf['app']['INTERLEAVE']:
        ranking_base = query_system(conf['app']['container_baseline'], query, rpp, page, session_id, logger, type='BASE')
        response = interleave(ranking_exp, ranking_base)
    else:
        response = single_ranking(ranking_exp)

    return jsonify(response)