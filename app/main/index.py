import threading
from . import main
from config import conf
from core.index import rest_index, cmd_index


@main.route("/index/<string:container_name>")
def index(container_name):
    if conf['app']['REST_QUERY']:
        rest_index(container_name)
    else:
        cmd_index(container_name)


@main.route("/index/bulk")
def index_bulk():
    container_list = conf["app"]["container_list"] + conf["app"]["container_list_recommendation"]
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