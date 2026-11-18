import threading
import time

import click
from app.extensions import db
from app.models import System
from app.services.system_service import rest_index
from flask import current_app
from flask.cli import with_appcontext


def init_db():
    """Use this function to setup a database with set of pre-registered users."""
    db.create_all()


def seed_db():
    """Register all configured systems in the database.

    Systems are identified by their name. A system whose name already exists in
    the database is skipped, so running this command multiple times does not
    create duplicate entries.
    """
    system_groups = [
        ("RANKING_CONTAINER_NAMES", "RANK", "LIVE"),
        ("RANKING_PRECOMPUTED_CONTAINER_NAMES", "RANK", "PRECOM"),
        ("RECOMMENDER_CONTAINER_NAMES", "REC", "LIVE"),
        ("RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES", "REC", "PRECOM"),
    ]

    existing_names = {name for (name,) in db.session.query(System.name).all()}

    systems = []
    for config_key, type_, system_type in system_groups:
        for system_name in current_app.config.get(config_key, []):
            if system_name in existing_names:
                current_app.logger.warning(
                    f"System '{system_name}' already exists in the database. Skipping."
                )
                continue
            systems.append(
                System(
                    name=system_name,
                    type=type_,
                    system_type=system_type,
                    num_requests=0,
                    num_requests_no_head=0,
                )
            )
            existing_names.add(system_name)

    db.session.add_all(systems)
    db.session.commit()
    return systems


def index_systems():
    """run indexing methods for all available containers"""
    container_list = (
        current_app.config["RANKING_CONTAINER_NAMES"]
        + current_app.config["RECOMMENDATION_CONTAINER_NAMES"]
        + current_app.config["PRECOM_CONTAINER_NAMES"]
        + current_app.config["PRECOM_RECOMMENDATION_CONTAINER_NAMES"]
    )

    time.sleep(30)

    threads = []
    for container_name in container_list:
        t = threading.Thread(target=rest_index, args=(container_name,))
        threads.append(t)
        t.start()


@click.command("init-db")
@with_appcontext
def init_db_command():
    init_db()


@click.command("seed-db")
@with_appcontext
def seed_db_command():
    seed_db()


@click.command("index-systems")
@with_appcontext
def index_systems():
    index_systems()
