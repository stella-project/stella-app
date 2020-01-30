import docker
from flask import Flask
from utils import create_logger
from config import conf
import logging
import time

SECS = 30
client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def index():
    ''' run indexing methods for all available containers '''
    container_list = list(conf["app"]["container_dict"].keys())

    cmd = 'python3 /script/index'

    time.sleep(SECS)

    for entry in container_list:
        container = client.containers.get(entry)
        logger = logging.getLogger("stella-app")
        logger.debug(f'Indexing container "{container}"...')
        exec_res = container.exec_run(cmd)


def get_least_served(container_dict):
    ''' return least served container '''
    least_served = list(container_dict.keys())[0]
    requests = container_dict[least_served]["requests"]

    for entry in container_dict.keys():
        if container_dict[entry]['requests'] < requests:
            least_served = entry
    logger = logging.getLogger("stella-app")
    logger.debug(f'least served container is: {least_served}')
    container_dict[least_served]['requests'] += 1
    return least_served


def create_app(config_name):

    index()

    create_logger("stella-app", f"{conf['log']['log_path']}/{conf['log']['log_file']}")
    logger = logging.getLogger("stella-app")
    logger.info("Logging started!")

    app = Flask(__name__)

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/stella/api/v1')

    return app
