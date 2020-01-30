import docker
import logging
import json
from flask import jsonify, request
from . import api
from core import get_least_served
from config import conf

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


@api.route("/recommendation/<string:docid>", methods=["GET"])
def recommendation(docid):
    container = client.containers.get('livivo-solr')

    cmd = 'python3 /script/recommend ' + docid

    logger = logging.getLogger("stella-app")
    logger.debug(f'produce recommendation with container: livivo-solr"...')
    exec_res = container.exec_run(cmd)
    exec_dict = json.loads(exec_res.output.decode("utf-8"))

    return jsonify(exec_dict)

