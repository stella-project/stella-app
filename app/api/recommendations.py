import docker
import logging
import json
from flask import jsonify, request, Flask
from . import api
from core import get_least_served
from config import conf
import ast
import requests

client = docker.DockerClient(base_url='unix://var/run/docker.sock')
app = Flask(__name__)


@api.route("/recommend_dataset/<string:doc_id>", methods=["GET"])

def recommand_dataset(doc_id):
    
    least_served = get_least_served(conf["app"]["container_dict_recommendation"])
    logger = logging.getLogger("stella-app")
    logger.debug(f'produce ranking with container: "{least_served}"...')
    if least_served == "recomm-sample":
        r= requests.get('http://recomm-sample:8889/api/recomm-sample/'+doc_id).json()
        return jsonify(r)
    else :
        r= requests.get('http://recomm_new:8888/api/recomm_new/'+doc_id).json()
        return jsonify(r)   

    
#--------------------------------------------------------------



@api.route('/dashboard')
def dashboard():
    entities = {"Research_data": resources.get_datasets_len(), "Publication": resources.get_publications_len()}
    itemetadata=resources.get_dataset_metadata().iloc[0]['_source']
    return render_template('dashboard.html',entities = entities,itemetadata=itemetadata)

@api.route('/', methods=['GET'])
def get():
    message = "GWS RecSys APP"
    return render_template('base.html', message=message)

@api.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404
