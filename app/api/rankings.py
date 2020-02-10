import docker
import logging
import json
import time
from flask import jsonify, request
from . import api
from core import get_least_served
from config import conf
from utils import create_dict_response

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


@api.route("/test/<string:container_name>", methods=["GET"])
def test(container_name):
    ''' run test script for given container name'''
    if request.method == 'GET':
        container = client.containers.get(container_name)

        cmd = 'python3 /script/test'

        out = container.exec_run(cmd)

        return "<h1> " + out.output.decode("utf-8") + " </h1>"


@api.route("/ranking/<string:query>", methods=["GET"])
def ranking(query):
    logger = logging.getLogger("stella-app")
    ''' return ranked documents in JSON-Format produced by least served container '''
    least_served = get_least_served(conf["app"]["container_dict"])

    container = client.containers.get(least_served)

    page = request.args.get('page', default=0,type=int)
    results_per_page = request.args.get('results_per_page', default=20,type=int)
    
    cmd = 'python3 /script/search {} {} {}'.format(query,results_per_page,page) 
    logger.debug('cmd: {}'.format(cmd))
     
    logger.debug(f'produce ranking with container: "{least_served}"...')
    ts_start =  time.time()
    ts = round(ts_start*1000)
    exec_res = container.exec_run(cmd)
    logger.debug(f'exec_res: {exec_res.output.decode("utf-8")}')
    result = json.loads(exec_res.output.decode('utf-8'))
    ts_end = time.time()
    # calc query execution time in ms
    q_time = round((ts_end-ts_start)*1000)
    
    num_found = len(result['itemlist'])

    # TODO implement paging based on get-params

    response_dict = create_dict_response(itemlist=result['itemlist'],params=request.args,q_time=q_time,container=least_served,num_found=num_found,ts=ts,page=page,results_per_page=results_per_page,query=query)
    
    return jsonify(response_dict)