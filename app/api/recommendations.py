

import docker
import logging
import json
from flask import jsonify, request
from . import api
from core import get_least_served
from config import conf

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


@app.route("/api/recommand_dataset/<string:doc_id>", methods=["GET"])
def recommand_dataset(doc_id):

    least_served = get_least_served(container_dict)
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    container = client.containers.get(least_served)
    cmd = 'python3 /script/recommand_dataset ' + doc_id
    logger = logging.getLogger("stella-app")
    logger.debug(f'produce ranking with container: "{least_served}"...')

    exec_res = container.exec_run(cmd)

    json_data = {}
    json_data = ast.literal_eval(exec_res.output.decode("utf-8"))
    json_data.update({'container': least_served})
    return jsonify(json_data)


@app.route('/dashboard')
def dashboard():
    entities = {"Research_data": resources.get_datasets_len(), "Publication": resources.get_publications_len()}
    itemetadata=resources.get_dataset_metadata().iloc[0]['_source']
    return render_template('dashboard.html',entities = entities,itemetadata=itemetadata)

@app.route('/', methods=['GET'])
def get():
    message = "GWS RecSys APP"
    return render_template('base.html', message=message)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404
