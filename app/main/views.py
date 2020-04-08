import docker
from . import main
from config import conf
from flask import render_template
import requests
import json

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


def rest_index(container_name, query, rpp, page):
    if conf['app']['DEBUG']:
        container = client.containers.get(container_name)
        ip_address = container.attrs['NetworkSettings']['Networks']['stella-app_default']['IPAddress']
        requests.get('http://' + ip_address + ':5000/index')
    else:
        requests.get(f'http://{container_name}:5000/index')


def cmd_index(container_name):
    container = client.containers.get(container_name)
    cmd = 'python3 /script/index'
    exec_res = container.exec_run(cmd)


@main.route("/index/<string:container_name>")
def index(container_name):
    if conf['app']['REST_QUERY']:
        rest_index(container_name)
    else:
        cmd_index(container_name)


def prep_list(container_list):
    data = []
    for container in container_list:
        data.append({'name': container,
                     'index': True})

    return data


@main.route("/")
def home():
    return render_template("table.html",
                           data=prep_list(container_list=conf["app"]["container_list"]),
                           title='List of running containers')



