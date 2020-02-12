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


@api.route("/ranking", methods=["GET"])
def ranking():
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
    logger.debug(f'produce ranking with container: "{container_name}"...')

    # no query ? -> Nothing to do
    if(query is None):
        return create_dict_response(status=1,ts=round(time.time()*1000))

    # return ranked documents in JSON-Format produced by least served container  
    else:
        cmd = 'python3 /script/search {} {} {}'.format(query,rpp,page) 
        ts_start =  time.time()
        ts = round(ts_start*1000)
        exec_res = container.exec_run(cmd)
        result = json.loads(exec_res.output.decode('utf-8'))
        ts_end = time.time()
        # calc query execution time in ms
        q_time = round((ts_end-ts_start)*1000)
        response_dict = create_dict_response(itemlist=result['itemlist'],params=request.args,q_time=q_time,container=container_name,num_found=result['num_found'],ts=ts,page=page,rpp=rpp,query=query)
    return jsonify(response_dict)