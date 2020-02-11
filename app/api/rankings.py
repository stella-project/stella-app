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
    query = request.args.get('query',None)
    container_name = request.args.get('container',None)
    
    if(container_name is None):
        container_name = get_least_served(conf["app"]["container_dict"])
    else:
        # check if container name exists
        if not (container_name in conf["app"]["container_dict"]):
            return "TODO: Implement"
            
    container = client.containers.get(container_name)

    logger.debug(f'produce ranking with container: "{container_name}"...')

    if(query is None):
        return "TODO: Implement"
    else:
        ''' return ranked documents in JSON-Format produced by least served container '''

        #requests.args.get('container',default=False,type=boolean)

        page = request.args.get('page', default=0,type=int)
        rpp = request.args.get('rpp', default=20,type=int)
        
        cmd = 'python3 /script/search {} {} {}'.format(query,rpp,page) 
        logger.debug('cmd: {}'.format(cmd))
         
        ts_start =  time.time()
        ts = round(ts_start*1000)
        exec_res = container.exec_run(cmd)
        logger.debug(f'exec_res: {exec_res.output.decode("utf-8")}')
        result = json.loads(exec_res.output.decode('utf-8'))
        ts_end = time.time()
        # calc query execution time in ms
        q_time = round((ts_end-ts_start)*1000)
        response_dict = create_dict_response(itemlist=result['itemlist'],params=request.args,q_time=q_time,container=container_name,num_found=result['num_found'],ts=ts,page=page,rpp=rpp,query=query)
    
    return jsonify(response_dict)