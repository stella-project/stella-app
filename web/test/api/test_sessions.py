import pytest


@pytest.mark.parametrize("type", ["ranker", "recommender"])
def test_exit_session(client, sessions, type):
    result = client.put(f"/stella/api/v1/sessions/{sessions[type].id}/exit")

    assert 204 == result.status_code


def test_exit_session_wrong_id(client):
    result = client.put(f"/stella/api/v1/sessions/NoID/exit")

    assert 404 == result.status_code


@pytest.mark.parametrize("type", ["ranker", "recommender"])
def test_post_user(client, sessions, type):
    result = client.post(
        f"/stella/api/v1/sessions/{sessions[type].id}/user",
        data={"site_user": "test"},
    )

    assert 201 == result.status_code


def test_post_user_wrong_id(client, sessions):
    result = client.post(
        f"/stella/api/v1/sessions/NoID/user",
        data={"site_user": "test"},
    )

    assert 404 == result.status_code
