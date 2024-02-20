import docker
import requests
from flask import current_app


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
