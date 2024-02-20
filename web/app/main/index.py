import threading
from . import main
from flask import current_app
from app.services.system_indexer_service import rest_index, cmd_index


@main.route("/index/<string:container_name>")
def index(container_name):
    if current_app.config["REST_QUERY"]:
        rest_index(container_name)
    else:
        cmd_index(container_name)
    return "Indexing started", 200


@main.route("/index/bulk")
def index_bulk():
    container_list = (
        current_app.config["RANKING_CONTAINER_NAMES"]
        + current_app.config["RECOMMENDER_CONTAINER_NAMES"]
    )
    threads = []
    if current_app.config["REST_QUERY"]:
        for container_name in container_list:
            t = threading.Thread(target=rest_index, args=(container_name,))
            threads.append(t)
            t.start()
    else:
        for container_name in container_list:
            t = threading.Thread(target=cmd_index, args=(container_name,))
            threads.append(t)
            t.start()
    return "Bulk indexing started", 200
