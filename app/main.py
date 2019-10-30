import urllib3
import json

import docker
from flask import Flask, jsonify, request

import logging
import utils
from config import conf

utils.create_logger("stella-app",f"{conf['log']['log_path']}/{conf['log']['log_file']}")
logger = logging.getLogger("stella-app")
logger.info("Logging started!")

client = docker.DockerClient(base_url='unix://var/run/docker.sock')
app = Flask(__name__)

def get_least_served(container_dict):
    ''' return least served container '''
    least_served = list(container_dict.keys())[0]
    requests = container_dict[least_served]["requests"]

    for entry in container_dict.keys():
        if container_dict[entry]['requests'] < requests:
            least_served = entry
    logger.debug(f'least served container is: {least_served}')
    container_dict[least_served]['requests'] += 1
    return least_served

def index():
    ''' run indexing methods for all available containers '''
    container_list = list(conf["app"]["container_dict"].keys())

    cmd = 'python /script/index'

    for entry in container_list:
        container = client.containers.get(entry)
        logger.debug(f'Indexing container "{container}"...')
        exec_res = container.exec_run(cmd)


@app.route("/")
def home():
    ''' display running containers '''

    html = "<h1> Here is a list of containers that are running: </h1> </br> <ul>"

    for c in client.containers.list():
        html += "<li> " + c.name + " </li>"

    html += " </ul>"

    return html


# @app.route("/stella/api/site/ranking/<string:query>", methods=["GET"])
# def ranking(query):
#     if request.method == 'GET':
#         http = urllib3.PoolManager()
#
#         url = 'http://solr:8983/solr/collection/select?q=' + query + '&wt=json'
#
#         connection = http.request('GET', url)
#         response = connection.data.decode('utf-8')
#
#         return jsonify(json.loads(response))


@app.route("/stella/api/site/ranking/<string:query>", methods=["GET"])
def ranking(query):
    ''' return ranked documents in JSON-Format produced by least served container '''
    least_served = get_least_served(conf["app"]["container_dict"])

    container = client.containers.get(least_served)

    cmd = 'python /script/search ' + query

    logger.debug(f'produce ranking with container: "{least_served}"...')
    exec_res = container.exec_run(cmd)
    exec_dict = json.loads(exec_res.output.decode("utf-8"))

    return jsonify(exec_dict)


@app.route("/stella/api/site/test/<string:container_name>", methods=["GET"])
def test(container_name):
    ''' run test script for given container name'''
    if request.method == 'GET':
        container = client.containers.get(container_name)

        cmd = 'python /script/test'

        out = container.exec_run(cmd)

        return "<h1> " + out.output.decode("utf-8") + " </h1>"


@app.route("/stella/api/site/recommendation/<int:doc_id>", methods=["GET"])
def recommendation(doc_id):
    pass


@app.route("/stella/api/site/feedback/<int:site_id>", methods=["POST"])
def feedback(site_id):
    pass


if __name__ == '__main__':
    index()
    logger.info("Starting app...")
    app.run(host='0.0.0.0', port=80, debug=False)