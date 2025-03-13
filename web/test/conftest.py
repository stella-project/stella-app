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
    create_return_recommendation_base,
    create_return_recommendation_experimental,
    create_results_recommendation,
    create_feedbacks_recommendation
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

# for recommedations starts here
### **Mock Requests for Recommenders**
@pytest.fixture
def mock_request_base_recommender(requests_mock):
    """Mock request to the baseline recommendation system."""
    container_name = "recommender_base"

    # Mock Docker network endpoint (same as ranking systems)
    requests_mock.get(
        f"http+docker://localhost/v1.47/containers/{container_name}/json",
        json={"NetworkSettings": {"Networks": {"stella-app_default": {"IPAddress": container_name}}}},
        status_code=200,
    )

    # Mock recommendation system response
    data = create_return_recommendation_base()
    requests_mock.get(f"http://{container_name}:5000/recommendation", json=data, status_code=200)
    return requests_mock


@pytest.fixture
def mock_request_experimental_recommender(requests_mock):
    """Mock request to the experimental recommendation system."""
    container_name = "recommender"

    requests_mock.get(
        f"http+docker://localhost/v1.47/containers/{container_name}/json",
        json={"NetworkSettings": {"Networks": {"stella-app_default": {"IPAddress": container_name}}}},
        status_code=200,
    )

    data = create_return_recommendation_experimental()
    requests_mock.get(f"http://{container_name}:5000/recommendation", json=data, status_code=200)
    return requests_mock


@pytest.fixture
def results_recommendation(sessions):
    """Fixture to create and store recommendation results separately from ranking results."""
    result_objs = create_results_recommendation(sessions)
    for result in result_objs.values():
        db.session.add(result)
    db.session.commit()
    return result_objs

@pytest.fixture
def feedback_recommendation(sessions):
    """Fixture to create and store recommendation feedback separately."""
    feedbacks = create_feedbacks_recommendation(sessions)
    for feedback in feedbacks.values():
        db.session.add(feedback)
    db.session.commit()
    return feedbacks



def request_recommendations(container_name, item_id, rpp, page):
    """
    Sends a request to the recommendation system inside a Docker container.

    @param container_name: The name of the recommendation system (str)
    @param item_id: The ID of the item for recommendations (str)
    @param rpp: Results per page (int)
    @param page: Page number (int)

    @return: JSON response with recommended items OR None if the request fails.
    """
    # Construct API endpoint
    url = f"http://{container_name}:5000/recommendation?item_id={item_id}&rpp={rpp}&page={page}"
    
    try:
        # Send GET request to the recommendation API
        response = requests.get(url, timeout=5)  # Timeout after 5 seconds
        response.raise_for_status()  # Raises an error for bad responses (4xx, 5xx)
        
        return response.json()  # Return the parsed JSON response
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"ERROR: Failed to fetch recommendations from {url} - {e}")
        return None