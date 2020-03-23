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
from config import conf
from utils import create_dict_response

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


# team-draft-interleaving
def tdi(item_dict_base, item_dict_exp):

    result = {}
    result_set = set([])

    max_length = len(item_dict_exp.values()) // 2

    pointer_exp = 0
    pointer_base = 0

    ranking_exp = list(item_dict_exp.values())
    ranking_base = list(item_dict_base.values())
    length_ranking_exp = len(ranking_exp)
    length_ranking_base = len(ranking_base)

    length_exp = 0
    length_base = 0

    pos = 1

    while pointer_exp < length_ranking_exp and pointer_base < length_ranking_base and len(result) < max_length:
        if length_exp < length_base or (length_exp == length_base and bool(random.getrandbits(1))):
            result.update({pos: {"docid": ranking_exp[pointer_exp], 'team': 'EXP'}})
            result_set.add(ranking_exp[pointer_exp])
            length_exp += 1
            pos += 1
        else:
            result.update({pos: {"docid":  ranking_base[pointer_base], 'team': 'BASE'}})
            result_set.add(ranking_base[pointer_base])
            length_base += 1
            pos += 1
        while pointer_exp < length_ranking_exp and ranking_exp[pointer_exp] in result_set:
            pointer_exp += 1
        while pointer_base < length_ranking_base and ranking_base[pointer_base] in result_set:
            pointer_base += 1
    return result


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
                            interleave=True,
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

        return 'ok'


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
    
    # no container_name specified? -> select least served container
    if(container_name is None):
        # container_name = get_least_served(conf["app"]["container_dict"])
        container_name = System.query.filter(System.name != conf['app']['container_baseline']).order_by(System.num_requests).first().name
    else:
        # container_name does not exist in config? -> Nothing to do
        if not (container_name in conf["app"]["container_dict"]):
            return create_dict_response(status=1, ts=round(time.time()*1000))

    if session_id is None:
        # make new session and get session_id as sid
        session = Session(start=datetime.now(),
                          system_ranking=System.query.filter_by(name=container_name).first().id,
                          exit=False,
                          sent=False)
        db.session.add(session)
        db.session.commit()
        session_id = session.id
    else:
        ranking_id = Session.query.get_or_404(session_id).system_ranking
        container_name = System.query.filter_by(id=ranking_id).first().name
            
    container = client.containers.get(container_name)
    logger.debug(f'produce ranking with container: "{container_name}"...')



    system = System.query.filter_by(name=container_name).first()
    system.num_requests += 1
    db.session.commit()

    # no query ? -> Nothing to do
    if(query is None):
        return create_dict_response(status=1,
                                    ts=round(time.time()*1000))

    # return ranked documents in JSON-Format produced by least served container  
    else:
        '''try:
            pass
        except Exception as e:
            raise e
        else:
            pass'''
        q_date = datetime.now().replace(microsecond=0)
        cmd = 'python3 /script/ranking {} {} {}'.format(query, rpp, page)
        ts_start =  time.time()
        ts = round(ts_start*1000)
        exec_res = container.exec_run(cmd)
        result = json.loads(exec_res.output.decode('utf-8'))
        ts_end = time.time()
        # calc query execution time in ms
        q_time = round((ts_end-ts_start)*1000)

        item_dict_exp = {i: result['itemlist'][i] for i in range(0, len(result['itemlist']))}

        ranking_exp = Result(session_id=session_id,
                         system_id=System.query.filter_by(name=container_name).first().id,
                         type='RANK',
                         q=query,
                         q_date=q_date,
                         q_time=q_time,
                         num_found=result['num_found'],
                         page=page,
                         rpp=rpp,
                         items=item_dict_exp)

        container_base = client.containers.get(conf['app']['container_baseline'])
        system = System.query.filter_by(name=conf['app']['container_baseline']).first()
        system.num_requests += 1
        db.session.commit()

        cmd = 'python3 /script/ranking {} {} {}'.format(query, rpp, page)
        ts_start = time.time()
        ts = round(ts_start*1000)
        exec_res = container_base.exec_run(cmd)
        result = json.loads(exec_res.output.decode('utf-8'))
        ts_end = time.time()
        # calc query execution time in ms
        q_time = round((ts_end-ts_start)*1000)

        item_dict_base = {i: result['itemlist'][i] for i in range(0, len(result['itemlist']))}

        ranking_base = Result(session_id=session_id,
                         system_id=System.query.filter_by(name=conf['app']['container_baseline']).first().id,
                         type='RANK',
                         q=query,
                         q_date=q_date,
                         q_time=q_time,
                         num_found=result['num_found'],
                         page=page,
                         rpp=rpp,
                         items=item_dict_base)

        item_dict_tdi = tdi(item_dict_base, item_dict_exp)
        ranking = Result(session_id=session_id,
                         system_id=System.query.filter_by(name=container_name).first().id,
                         type='RANK',
                         q=query,
                         q_date=q_date,
                         q_time=q_time,
                         num_found=result['num_found'],
                         page=page,
                         rpp=rpp,
                         items=item_dict_tdi)
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

        # response_dict = create_dict_response(itemlist=result['itemlist'],
        #                                      params=request.args,
        #                                      q_time=q_time,
        #                                      container=container_name,
        #                                      num_found=result['num_found'],
        #                                      ts=ts,
        #                                      page=page,
        #                                      rpp=rpp,
        #                                      query=query,
        #                                      sid=session_id,
        #                                      rid=ranking_id)
        response_dict = create_dict_response(itemlist=list(item_dict_tdi.values()),
                                             params=request.args,
                                             q_time=q_time,
                                             container=container_name,
                                             num_found=result['num_found'],
                                             ts=ts,
                                             page=page,
                                             rpp=rpp,
                                             query=query,
                                             sid=session_id,
                                             rid=ranking_id)
        return jsonify(response_dict)


# alternative way to get rankings from container via rest (test implementation)
@api.route('/ranking2', methods=['GET'])
def ranking_rest():
    logger = logging.getLogger("stella-app")

    # look for mandatory GET-parameters (query, container_name)
    query = request.args.get('query',None)
    container_name = request.args.get('container',None)

    # Look for optional GET-parameters and set default values
    page = request.args.get('page', default=0,type=int)
    rpp = request.args.get('rpp', default=20,type=int)

    # no container_name specified? -> select least served container
    if(container_name is None):
        container_name = get_least_served(conf["app"]["container_dict"])
    else:
        # container_name does not exist in config? -> Nothing to do
        if not (container_name in conf["app"]["container_dict"]):
            return create_dict_response(status=1,ts=round(time.time()*1000))

    container = client.containers.get(container_name)    
    logger.debug(f'produce ranking (REST) with container: "{container_name}"...')

    # no query ? -> Nothing to do
    if(query is None):
        return create_dict_response(status=1,ts=round(time.time()*1000))
    else:
        ts_start =  time.time()
        ts = round(ts_start*1000)
        result = requests.get(f'http://{container_name}:5000/ranking',params={'query':query})
        ts_end = time.time()
        result = result.json()
        # calc query execution time in ms
        q_time = round((ts_end-ts_start)*1000)
        response_dict = create_dict_response(itemlist=result['itemlist'],params=request.args,q_time=q_time,container=container_name,num_found=result['num_found'],ts=ts,page=page,rpp=rpp,query=query)
    return jsonify(response_dict)
