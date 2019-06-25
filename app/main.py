import urllib3
import json

import docker
from flask import Flask, jsonify, request

app = Flask(__name__)

container_dict = {"lucene": {"requests": 0},
                  "solr": {"requests": 0}}


def get_least_served(container_dict):
    least_served = list(container_dict.keys())[0]
    requests = container_dict[least_served]["requests"]

    for entry in container_dict.keys():
        if container_dict[entry]['requests'] < requests:
            least_served = entry

    container_dict[least_served]['requests'] += 1
    return least_served


def index():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    container_list = list(container_dict.keys())

    cmd = 'python /script/index'

    for entry in container_list:
        container = client.containers.get(entry)
        exec_res = container.exec_run(cmd)


@app.route("/")
def home():
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

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
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    least_served = get_least_served(container_dict)

    container = client.containers.get(least_served)

    cmd = 'python /script/search ' + query

    exec_res = container.exec_run(cmd)

    exec_dict = json.loads(exec_res.output.decode("utf-8"))

    return jsonify(exec_dict)


@app.route("/stella/api/site/test/<string:container_name>", methods=["GET"])
def test(container_name):
    if request.method == 'GET':
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
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
    app.run(host='0.0.0.0', port=80, debug=False)
