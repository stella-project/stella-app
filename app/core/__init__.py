from typing import List
import threading
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
from .index import rest_index, cmd_index

basedir = os.path.abspath(os.path.dirname(__file__))

SECS = 30
client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def index():
    ''' run indexing methods for all available containers '''
    container_list = conf["app"]["container_list"] + conf["app"]["container_list_recommendation"] + conf["app"]["container_precom_list"] + conf["app"]["container_precom_list_recommendation"]

    time.sleep(SECS)

    threads = []

    if conf['app']['REST_QUERY']:
        for container_name in container_list:
            t = threading.Thread(target=rest_index, args=(container_name,))
            threads.append(t)
            t.start()
    else:
        for container_name in container_list:
            t = threading.Thread(target=cmd_index, args=(container_name,))
            threads.append(t)
            t.start()


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

    if conf['app']['BULK_INDEX']:
        index()

    create_logger("stella-app", f"{conf['log']['log_path']}/{conf['log']['log_file']}")
    logger = logging.getLogger("stella-app")
    logger.info("Logging started!")

    app = Flask(__name__, template_folder='../templates')

    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(Path(basedir).parent, 'data-dev.sqlite')

    app.config['DEBUG'] = False
    app.config['POSTGRES_USER'] = 'postgres'
    app.config['POSTGRES_PW'] = 'postgres'
    app.config['POSTGRES_URL'] = 'db:5432'
    app.config['POSTGRES_DB'] = 'postgres'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{user}:{pw}@{url}/{db}'.format(user='postgres',
                                                                           pw='postgres',
                                                                           url='db:5432',
                                                                           db='postgres')

    db.init_app(app)
    with app.app_context():
        db.drop_all()
        db.create_all()

        # add ranking systems to database
        ranksys: List[System] = [System(name=sysname,
                                        type='RANK',
                                        system_type='LIVE',
                                        num_requests=0,
                                        num_requests_no_head=0) for sysname in conf['app']['container_list']] + \
                                [System(name=sysname,
                                        type='RANK',
                                        system_type='PRECOM',
                                        num_requests=0,
                                        num_requests_no_head=0) for sysname in conf['app']['container_precom_list']]

        db.session.add_all(ranksys)
        db.session.commit()

        # add recommendation systems to database
        ranksys: List[System] = [System(name=sysname,
                                        type='REC',
                                        system_type='LIVE',
                                        num_requests=0,
                                        num_requests_no_head=0) for sysname in conf['app']['container_list_recommendation']] + \
                                [System(name=sysname,
                                        type='REC',
                                        system_type='PRECOM',
                                        num_requests=0,
                                        num_requests_no_head=0) for sysname in conf['app']['container_precom_list_recommendation']]
        db.session.add_all(ranksys)
        db.session.commit()

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/stella/api/v1')

    return app
