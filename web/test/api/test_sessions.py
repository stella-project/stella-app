import pytest


@pytest.mark.parametrize(
    "system", ["ranker", "recommender", "ranker_base", "recommender_base"]
)
def test_exit_session(client, sessions, system):
    result = client.put(f"/stella/api/v1/sessions/{sessions[system].id}/exit")
    assert 204 == result.status_code


def test_exit_session_wrong_id(client):
    result = client.put(f"/stella/api/v1/sessions/NoID/exit")
    assert 404 == result.status_code


@pytest.mark.parametrize(
    "system", ["ranker", "recommender", "ranker_base", "recommender_base"]
)
def test_post_user(client, sessions, system):
    result = client.post(
        f"/stella/api/v1/sessions/{sessions[system].id}/user",
        data={"site_user": "test"},
    )
    assert 201 == result.status_code


def test_post_user_wrong_id(client, sessions):
    result = client.post(
        f"/stella/api/v1/sessions/NoID/user",
        data={"site_user": "test"},
    )

    assert 404 == result.status_code
