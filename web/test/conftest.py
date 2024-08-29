from app.app import db, create_app
import os
import pytest

from app.commands import init_db
from app.models import Session
import random
from app.services.session_service import create_new_session

from .create_test_data import (
    create_systems,
    create_result,
    create_feedback,
    create_experimental_return,
)

import os


@pytest.fixture()
def app():
    # setup flask app

    app = create_app()

    # setup database
    with app.app_context():
        init_db()

    yield app

    # Teardown code, if necessary
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def db_session(app):
    """Ensure that each test has a clean session."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        options = dict(bind=connection, binds={})
        session = db._make_scoped_session(options=options)
        db.session = session

        yield session

        transaction.rollback()
        connection.close()
        session.remove()


# Data fixtures
@pytest.fixture
def systems():
    systems_ranker = create_systems(type="ranker")
    systems_recommender = create_systems(type="recommender")

    db.session.add_all(systems_ranker)
    db.session.add_all(systems_recommender)
    db.session.commit()

    return {
        "ranker": systems_ranker,
        "recommender": systems_recommender,
    }


@pytest.fixture
def sessions(systems):
    ranker_session_id = create_new_session(
        container_name="ranker_base", sid=None, type="ranker"
    )
    ranker_session = db.session.query(Session).filter_by(id=ranker_session_id).first()

    recommender_session_id = create_new_session(
        container_name="recommender_base", sid=None, type="recommender"
    )
    recommender_session = (
        db.session.query(Session).filter_by(id=recommender_session_id).first()
    )

    return {
        "ranker": ranker_session,
        "recommender": recommender_session,
    }


@pytest.fixture
def results(sessions):
    ranker_result = create_result(sessions, type="ranker")
    recommender_result = create_result(sessions, type="recommender")

    db.session.add_all([ranker_result, recommender_result])
    db.session.commit()

    return {
        "ranker": ranker_result,
        "recommender": recommender_result,
    }


@pytest.fixture
def feedback(sessions):
    number_of_feedbacks = random.randint(1, 4)
    feedbacks_ranker = create_feedback(number_of_feedbacks, sessions, type="ranker")
    db.session.add_all(feedbacks_ranker)

    feedbacks_recommender = create_feedback(
        number_of_feedbacks, sessions, type="recommender"
    )
    db.session.add_all(feedbacks_recommender)

    db.session.commit()

    return {
        "ranker": feedbacks_ranker,
        "recommender": feedbacks_recommender,
    }


@pytest.fixture
def mock_request_experimental_system(requests_mock):
    """Fixture for mocking the request to the experimental system."""
    container_name = "ranker"

    # Mock the debug docker network endpoint
    requests_mock.get(
        f"http+docker://localhost/v1.45/containers/{container_name}/json",
        json={
            "NetworkSettings": {
                "Networks": {"stella-app_default": {"IPAddress": "localhost"}}
            }
        },
        status_code=200,
    )

    # Mock the experimental system ranking endpoint
    data = create_experimental_return()
    requests_mock.get("http://localhost:5000/ranking", json=data, status_code=200)
    return requests_mock
