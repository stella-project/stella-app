import os

import pytest

from ..create_test_data import (
    create_feedbacks,
    create_return_base,
    create_return_experimental,
)

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

    def test_ranking(
        self,
        mock_request_system,
        client,
        results,
        sessions,
    ):
        """Test the ranking endpoint with a randomly sampled system. Since the database is empty it will always return the only experimental system"""
        query_params = {"query": "Test Query"}
        result = client.get(self.URL, query_string=query_params)
        data = result.json

        assert 200 == result.status_code
        assert "hits" in data
        assert data["hits"].keys() == {"hits", "max_score", "total"}

        response = create_return_experimental()
        assert data == response

    def test_ranking_fixed_container(
        self,
        mock_request_base_system,
        client,
        results,
        sessions,
    ):
        """Test the ranking endpoint with a specified system."""
        query_params = {"query": "Test Query", "container": "ranker_base"}
        result = client.get(self.URL, query_string=query_params)
        data = result.json

        assert 200 == result.status_code
        assert data["header"]["q"] == query_params["query"]
        assert data["header"]["container"].keys() == {"exp"}  # Only one system
        assert (
            data["header"]["container"]["exp"] == "ranker_base"
        )  # System is base system

        response = create_return_base()
        ranking = [r["docid"] for r in data["body"].values()]
        assert ranking == response["itemlist"]

# TODO: Fix interleaving
# @pytest.mark.skipif(
#     running_in_ci, reason="Test requires Docker and will not run in CI environment"
# )
# def test_ranking_interleaved(
#     app,
#     client,
#     db_session,
#     results,
#     sessions,
#     mock_request_system,
#     mock_request_base_system,
# ):
#     app.config["INTERLEAVE"] = True
#     query_params = {"query": "Test Query"}
#     result = client.get("/stella/api/v1/ranking", query_string=query_params)

#     data = result.json
#     assert 200 == result.status_code
#     assert "body" in data
#     # Given the randomness of the interleaving, we can only check for the keys
#     assert (
#         "_score" in data["body"][0]
#         or "_score" in data["body"][1]
#         or "_score" in data["body"][2]
#     )


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
