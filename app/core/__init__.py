from typing import List

import docker
from flask import Flask
from utils import create_logger
from config import conf
import logging
import time
from flask_sqlalchemy import SQLAlchemy
import os
from pathlib import Path

from .models import db, System, Session


basedir = os.path.abspath(os.path.dirname(__file__))

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

    # index()

    create_logger("stella-app", f"{conf['log']['log_path']}/{conf['log']['log_file']}")
    logger = logging.getLogger("stella-app")
    logger.info("Logging started!")

    app = Flask(__name__, template_folder='../templates')

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(Path(basedir).parent, 'data-dev.sqlite')
    db.init_app(app)
    with app.app_context():
        db.drop_all()
        db.create_all()

        # add ranking systems to database
        ranksys: List[System] = [System(name=sysname, type='RANK', num_requests=0) for sysname in conf['app']['container_list']]
        db.session.add_all(ranksys)
        db.session.commit()

        # add recommendation systems to database
        ranksys: List[System] = [System(name=sysname, type='REC', num_requests=0) for sysname in conf['app']['container_list_recommendation']]
        db.session.add_all(ranksys)
        db.session.commit()

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/stella/api/v1')

    return app
