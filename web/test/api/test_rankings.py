from app.models import System, Result
from ..create_test_data import create_feedback


def test_ranking_no_query(client, systems):
    result = client.get("/stella/api/v1/ranking")
    data = result.json
    assert 200 == result.status_code
    assert "response_header" in data
    assert "response" in data


def test_ranking_cached_query_session(client, results, sessions):
    session_id = sessions["ranker"].id
    result = client.get(f"/stella/api/v1/ranking?query=test&sid={session_id}")

    data = result.json
    assert 200 == result.status_code
    assert data["body"] == results["ranker"].items
    assert data["header"]["sid"] == session_id


def test_ranking_from_db(client, results, sessions):
    result_id = results["ranker"].id
    result = client.get(f"/stella/api/v1/ranking/{result_id}")

    data = result.json
    assert 200 == result.status_code
    assert data["rid"] == result_id


def test_ranking_from_db_not_existing(client, results, sessions):
    result_id = 999
    result = client.get(f"/stella/api/v1/ranking/{result_id}")

    data = result.json
    assert 404 == result.status_code


def test_post_feedback(client, results, sessions):
    feedbacks = create_feedback(1, sessions, type="ranker")

    data = {
        "clicks": feedbacks[0].clicks,
    }

    result = client.post(
        f"/stella/api/v1/ranking/{results['ranker'].id}/feedback",
        data=data,
    )

    assert 201 == result.status_code


def test_post_feedback_wrong_id(client, results, sessions):
    feedbacks = create_feedback(1, sessions, type="ranker")

    data = {
        "clicks": feedbacks[0].clicks,
    }

    result = client.post(
        f"/stella/api/v1/ranking/999/feedback",
        data=data,
    )

    assert 404 == result.status_code
