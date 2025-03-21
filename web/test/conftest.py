from unittest.mock import AsyncMock, patch

import pytest
from aioresponses import aioresponses
from app.app import create_app, db
from app.models import Session

from .create_test_data import (
    create_feedbacks,
    create_results,
    create_return_base,
    create_return_experimental,
    create_sessions,
    create_systems,
)


@pytest.fixture()
def app():
    # setup flask app

    app = create_app("test")

    # setup database
    with app.app_context():
        db.create_all()

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
def mock_request_base_system():
    """Fixture to mock aiohttp requests with predefined attributes."""
    container_name = "ranker_base"
    query = "Test Query"
    rpp = 10
    page = 0
    mock_url = (
        f"http://{container_name}:5000/ranking?query={query}&rpp={rpp}&page={page}"
    )
    mock_response = create_return_base()

    with aioresponses() as mocked:
        mocked.get(mock_url, payload=mock_response)
        yield {
            "mock": mocked,  # The aioresponses instance
            "container_name": container_name,
            "query": query,
            "rpp": rpp,
            "page": page,
            "mock_url": mock_url,
            "mock_response": mock_response,
        }


@pytest.fixture
def mock_request_exp_system():
    """Fixture to mock aiohttp requests with predefined attributes."""
    container_name = "ranker"
    query = "Test Query"
    rpp = 10
    page = 0
    mock_url = (
        f"http://{container_name}:5000/ranking?query={query}&rpp={rpp}&page={page}"
    )
    mock_response = create_return_experimental()

    with aioresponses() as mocked:
        mocked.get(mock_url, payload=mock_response)

        yield {
            "mock": mocked,
            "container_name": container_name,
            "query": query,
            "rpp": rpp,
            "page": page,
            "mock_url": mock_url,
            "mock_response": mock_response,
        }


@pytest.fixture
def mock_request_results():
    """Mock `request_results_from_container` with different responses based on input."""

    async def mock_side_effect(session, container_name, query, rpp, page):
        """Return different mocked responses based on parameters."""
        if container_name == "ranker_base":
            return create_return_base()
        elif container_name == "ranker":
            return create_return_experimental()
        else:
            return {"results": []}

    with patch(
        "app.services.ranking_service.request_results_from_container",
        new_callable=AsyncMock,
    ) as mock_func:
        mock_func.side_effect = mock_side_effect
        yield mock_func
