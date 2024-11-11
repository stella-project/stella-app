from app.app import db, create_app
import pytest

from app.commands import init_db
from app.models import Session

from .create_test_data import (
    create_systems,
    create_sessions,
    create_results,
    create_feedbacks,
    create_return_base,
    create_return_experimental,
)


@pytest.fixture()
def app():
    # setup flask app

    app = create_app("test")

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


@pytest.fixture
def systems():
    test_systems = create_systems()
    for system in test_systems.values():
        db.session.add(system)
    db.session.commit()

    return test_systems


@pytest.fixture
def sessions(systems):
    test_sessions = create_sessions(systems)
    for system, session_id in test_sessions.items():
        session_obj = db.session.query(Session).filter_by(id=session_id).first()
        test_sessions[system] = session_obj
    return test_sessions


@pytest.fixture
def results(sessions):
    result_objs = create_results(sessions)
    for result in result_objs.values():
        db.session.add(result)
    db.session.commit()
    return result_objs


@pytest.fixture
def feedback(sessions):
    feedbacks = create_feedbacks(sessions)
    for feedback in feedbacks.values():
        db.session.add(feedback)
    db.session.commit()

    return feedbacks


@pytest.fixture
def mock_request_base_system(requests_mock):
    """Fixture for mocking the request to the experimental system."""
    container_name = "ranker_base"

    # Mock the debug docker network endpoint
    requests_mock.get(
        f"http+docker://localhost/v1.47/containers/{container_name}/json",
        json={
            "NetworkSettings": {
                "Networks": {"stella-app_default": {"IPAddress": container_name}}
            }
        },
        status_code=200,
    )

    # Mock the experimental system ranking endpoint
    data = create_return_base()
    requests_mock.get(
        f"http://{container_name}:5000/ranking", json=data, status_code=200
    )
    return requests_mock


@pytest.fixture
def mock_request_experimental_system(requests_mock):
    """Fixture for mocking the request to the experimental system."""
    container_name = "ranker"

    # Mock the debug docker network endpoint
    requests_mock.get(
        f"http+docker://localhost/v1.47/containers/{container_name}/json",
        json={
            "NetworkSettings": {
                "Networks": {"stella-app_default": {"IPAddress": container_name}}
            }
        },
        status_code=200,
    )

    # Mock the experimental system ranking endpoint
    data = create_return_experimental()
    requests_mock.get(
        f"http://{container_name}:5000/ranking", json=data, status_code=200
    )
    return requests_mock
