import json
import os

import pytest

from ..create_test_data import (
    create_feedbacks,
    create_results,
    create_return_recommendation_base,
    create_return_recommendation_experimental,
)

running_in_ci = os.getenv("CI") == "true"


class TestRecommendation:
    URL = "/stella/api/v1/recommendation"

    def test_ranking_no_query(self, client, systems):
        result = client.get(self.URL)
        data = result.json
        assert 400 == result.status_code

    def test_recommendation(
        self,
        mock_request_recommender,
        client,
        results,
        sessions,
    ):
        """Test the recommendation endpoint with a randomly sampled system. Since the database is empty it will always return the only experimental system"""
        # Not interleaved
        query_params = {"itemid": "test_item"}
        result = client.get(self.URL, query_string=query_params)
        data = result.json

        assert 200 == result.status_code
        assert "hits" in data
        assert data["hits"].keys() == {"hits", "max_score", "total"}

        response = create_return_recommendation_experimental()
        assert data == response

    def test_ranking_fixed_container(
        self, mock_request_base_recommender, client, results, sessions
    ):
        """Test the ranking endpoint with a specified system."""
        # Not interleaved
        query_params = {"itemid": "test_item", "container": "recommender_base"}
        result = client.get(self.URL, query_string=query_params)
        data = result.json

        assert 200 == result.status_code
        assert data["header"]["q"] == query_params["itemid"]
        assert data["header"]["container"].keys() == {"exp"}  # Only one system
        # System is base system
        assert data["header"]["container"]["exp"] == "recommender_base"

        assert data["body"].keys() == {
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
        }
        response = create_return_recommendation_base()

        for i in range(1, 11):
            assert data["body"][str(i)].keys() == {"docid", "type"}
            assert data["body"][str(i)]["docid"] == f"doc{i}"


@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
class TestPostRecommendationFeedback:
    URL = "/stella/api/v1/recommendation/{}/feedback"

    def test_post_feedback_endpoint(self, client, results, sessions):
        """Test posting feedback for a recommendation."""
        feedbacks = create_feedbacks(sessions)
        data = {"clicks": feedbacks["recommender_base"].clicks}
        result = client.post(self.URL.format(results["recommender"].id), json=data)
        assert 201 == result.status_code

    def test_post_feedback_wrong_id(self, client, results, sessions):
        """Test posting feedback to a non-existing recommendation ID."""
        feedbacks = create_feedbacks(sessions)
        data = {"clicks": feedbacks["recommender_base"].clicks}
        result = client.post(self.URL.format("999"), json=data)
        assert 404 == result.status_code

    def test_post_feedback_no_clicks(self, client, results, sessions):
        """Test posting feedback without clicks."""
        feedbacks = create_feedbacks(sessions)
        data = {}
        result = client.post(self.URL.format(results["recommender"].id), json=data)
        assert 400 == result.status_code


def test_ranking_from_db(client, results, sessions):
    result_id = results["ranker"].id
    result = client.get(f"/stella/api/v1/recommendation/{result_id}")

    data = result.json
    assert 200 == result.status_code
    assert data["rid"] == result_id
