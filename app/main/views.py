import docker
from . import main

client = docker.DockerClient(base_url='unix://var/run/docker.sock')


@main.route("/")
def home():
    ''' display running containers '''

    html = "<h1> Here is a list of containers that are running: </h1> </br> <ul>"

    for c in client.containers.list():
        html += "<li> " + c.name + " </li>"

    html += " </ul>"

    return html