from . import main
from flask import render_template, current_app


def prep_list(container_list):
    data = []
    for container in container_list:
        data.append({"name": container, "index": True})

    return data


@main.route("/")
def home():
    container_list = (
        current_app.config["RANKING_CONTAINER_NAMES"]
        + current_app.config["RECOMMENDER_CONTAINER_NAMES"]
        + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
        + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
    )
    return render_template(
        "table.html",
        data=prep_list(container_list=container_list),
        title="List of running containers",
    )
