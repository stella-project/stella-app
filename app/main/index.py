from . import main
from config import conf
from core.index import rest_index, cmd_index


@main.route("/index/<string:container_name>")
def index(container_name):
    if conf['app']['REST_QUERY']:
        rest_index(container_name)
    else:
        cmd_index(container_name)