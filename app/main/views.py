from . import main
from config import conf
from flask import render_template


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
