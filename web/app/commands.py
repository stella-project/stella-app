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
    db.drop_all()
    db.create_all()


def seed_db():
    """Use this function to setup a database with set of pre-registered users."""
    # TODO: Make this more verbose and configurable
    # add ranking systems to database
    systems = []
    for system_name in current_app.config["RANKING_CONTAINER_NAMES"]:
        systems.append(
            System(
                name=system_name,
                type="RANK",
                system_type="LIVE",
                num_requests=0,
                num_requests_no_head=0,
            )
        )

    for system_name in current_app.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"]:
        systems.append(
            System(
                name=system_name,
                type="RANK",
                system_type="PRECOM",
                num_requests=0,
                num_requests_no_head=0,
            )
        )

    db.session.add_all(systems)
    db.session.commit()

    # add recommendation systems to database
    systems = []
    for system_name in current_app.config["RECOMMENDER_CONTAINER_NAMES"]:
        systems.append(
            System(
                name=system_name,
                type="REC",
                system_type="LIVE",
                num_requests=0,
                num_requests_no_head=0,
            )
        )

    for sysname in current_app.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"]:
        systems.append(
            System(
                name=sysname,
                type="REC",
                system_type="PRECOM",
                num_requests=0,
                num_requests_no_head=0,
            )
        )

    db.session.add_all(systems)
    db.session.commit()


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
