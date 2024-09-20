import os
import pytest
from ..create_test_data import create_feedbacks, create_return_experimental

running_in_ci = os.getenv("CI") == "true"


def test_ranking_from_db(client, results, sessions):
    result_id = results["ranker"].id
    result = client.get(f"/stella/api/v1/ranking/{result_id}")

    data = result.json
    assert 200 == result.status_code
    assert data["rid"] == result_id


class TestRanking:
    URL = "/stella/api/v1/ranking"

    def test_ranking_no_query(self, client, systems):
        result = client.get(self.URL)
        data = result.json
        assert 400 == result.status_code

    @pytest.mark.skipif(
        running_in_ci, reason="Test requires Docker and will not run in CI environment"
    )
    def test_ranking(self, client, results, sessions, mock_request_base_system):
        result = client.get(self.URL + "?query=test query&container=ranker_base")
        data = result.json

        assert 200 == result.status_code
        assert "header" in data
        assert "body" in data

        # only one key since we directly request a container
        assert data["header"]["container"].keys() == {"exp"}
        assert data["header"]["container"]["exp"] == "ranker_base"

    @pytest.mark.skipif(
        running_in_ci, reason="Test requires Docker and will not run in CI environment"
    )
    def test_ranking_experimental(
        self,
        app,
        client,
        db_session,
        results,
        sessions,
        mock_request_experimental_system,
    ):
        result = client.get(self.URL + "?query=test query&container=ranker")
        data = result.json

        response = create_return_experimental()

        assert 200 == result.status_code
        assert data == response


@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
def test_ranking_interleaved(
    app,
    client,
    db_session,
    results,
    sessions,
    mock_request_experimental_system,
    mock_request_base_system,
):
    app.config["INTERLEAVE"] = True
    result = client.get("/stella/api/v1/ranking?query=test query&container=ranker")

    data = result.json
    print(data)
    assert 200 == result.status_code
    assert "body" in data
    # Given the randomness of the interleaving, we can only check for the keys
    assert (
        "_score" in data["body"][0]
        or "_score" in data["body"][1]
        or "_score" in data["body"][2]
    )


class TestPostFeedback:
    URL = "/stella/api/v1/ranking/{}/feedback"

    def test_post_feedback(self, client, results, sessions):
        feedbacks = create_feedbacks(sessions)
        data = {
            "clicks": feedbacks["ranker_base"].clicks,
        }
        result = client.post(self.URL.format(results["ranker"].id), data=data)
        assert 201 == result.status_code

    def test_post_feedback_wrong_id(self, client, results, sessions):
        feedbacks = create_feedbacks(sessions)
        data = {
            "clicks": feedbacks["ranker_base"].clicks,
        }
        result = client.post(self.URL.format("999"), data=data)
        assert 404 == result.status_code
