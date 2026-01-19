from . import main
from flask import render_template, current_app, jsonify, request
from app.models import db, System
from config import parse_systems_config


def prep_list(container_list, db_systems):
    data = []
    for container in container_list:
        if container in db_systems:
            data.append(
                {
                    "name": container,
                    "index": True,
                    "status": db_systems[container].get("system_type"),
                }
            )
        else:
            data.append({"name": container, "index": True, "status": "NOT IN DB-APP"})

    return data


@main.route("/")
def home():
    container_list = (
        current_app.config["RANKING_CONTAINER_NAMES"]
        + current_app.config["RECOMMENDER_CONTAINER_NAMES"]
        + current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]
        + current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]
    )
    db_systems = db.session.query(System).all()
    db_systems = {system.name: system.serialize for system in db_systems}
    data = prep_list(container_list, db_systems)

    return render_template(
        "table.html",
        data=data,
        title="List of running containers",
    )


@main.route("/get_systems_config")
def get_systems_config():

    return jsonify(current_app.config["SYSTEMS_CONFIG"]), 200


@main.route("/set_systems_config", methods=["POST"])
def set_systems_config():

    payload = request.get_json(silent=True)  # dict (or None)
    if payload is None:
        return jsonify({"ok": False, "error": "Invalid/missing JSON"}), 400
    
    try:
        (
            current_app.config["RANKING_CONTAINER_NAMES"],
            current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"],
            current_app.config["RANKING_BASELINE_CONTAINER"],
            current_app.config["RECOMMENDER_CONTAINER_NAMES"],
            current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"],
            current_app.config["RECOMMENDER_BASELINE_CONTAINER"],
            current_app.config["SYSTEMS_CONFIG"],
        ) = parse_systems_config(payload)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    current_app.logger.debug(f"SYSTEMS_CONFIG updated: {current_app.config['SYSTEMS_CONFIG']}")

    return jsonify({"msg": "SYSTEMS_CONFIG updated!"}), 200