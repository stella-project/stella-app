import docker
import logging
import json
from flask import jsonify, request
from . import api
from core import get_least_served
from config import conf

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
    ''' return ranked documents in JSON-Format produced by least served container '''
    least_served = get_least_served(conf["app"]["container_dict"])

    container = client.containers.get(least_served)

    cmd = 'python3 /script/search ' + query

    logger = logging.getLogger("stella-app")
    logger.debug(f'produce ranking with container: "{least_served}"...')
    exec_res = container.exec_run(cmd)
    exec_dict = json.loads(exec_res.output.decode("utf-8"))

    return jsonify(exec_dict)
