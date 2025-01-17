import docker
import requests

from flask import current_app
from app.models import db, System


import os
if os.name == 'nt':  # Windows
    client = docker.DockerClient(base_url="npipe:////./pipe/docker_engine")
else:  # Unix-based systems like Linux or macOS
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")


def rest_index(container_name):
    if current_app.config["DEBUG"]:
        container = client.containers.get(container_name)
        ip_address = container.attrs["NetworkSettings"]["Networks"][
            "stella-app_default"
        ]["IPAddress"]
        requests.get(f"http://{ip_address}:5000/index")
    else:
        requests.get(f"http://{container_name}:5000/index")


def cmd_index(container_name):
    container = client.containers.get(container_name)
    cmd = "python3 /script/index"
    exec_res = container.exec_run(cmd)


def get_least_served_system(query):
    if query in current_app.config["HEAD_QUERIES"]:
        container_name = (
            db.session.query(System)
            .filter(System.name != current_app.config["RANKING_BASELINE_CONTAINER"])
            .filter(
                System.name.notin_(
                    current_app.config["RECOMMENDER_CONTAINER_NAMES"]
                    + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
                )
            )
            .order_by(System.num_requests)
            .first()
            .name
        )
    else:
        # Select least served container
        container_name = (
            db.session.query(System)
            .filter(System.name != current_app.config["RANKING_BASELINE_CONTAINER"])
            .filter(
                System.name.notin_(
                    current_app.config["RECOMMENDER_CONTAINER_NAMES"]
                    + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
                    + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
                )
            )
            .order_by(System.num_requests_no_head)
            .first()
            .name
        )
    return container_name
