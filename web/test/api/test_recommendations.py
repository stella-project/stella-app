import json
import os
import pytest
from ..create_test_data import create_feedbacks, create_return_recommendation

running_in_ci = os.getenv("CI") == "true"





def test_recommendation_from_db(client, results, sessions):
    """Test fetching recommendation from DB by ID"""
    result_id = results["recommender"].id
    result = client.get(f"/stella/api/v1/recommendation/{result_id}")

    data = result.json
    assert 200 == result.status_code
    assert data["rid"] == result_id


class TestRecommendations:
    URL = "/stella/api/v1/recommendation"

    def test_recommendation_no_itemid(self, client, systems):
        """Test recommendation without itemid (should fail)"""
        result = client.get(self.URL)
        data = result.json
        assert 400 == result.status_code
        assert "error" in data

    @pytest.mark.skipif(
        running_in_ci, reason="Test requires Docker and will not run in CI environment"
    )
    def test_recommendation(self, client, results, sessions, mock_request_base_recommender_system):
        """Test recommendation with valid parameters"""
        result = client.get(self.URL + "?itemid=test_item&container=recommender_base")
        data = result.json

        assert 200 == result.status_code
        assert "header" in data
        assert "body" in data

        # only one key since we directly request a container
        assert data["header"]["container"].keys() == {"exp"}
        assert data["header"]["container"]["exp"] == "recommender_base"

    @pytest.mark.skipif(
        running_in_ci, reason="Test requires Docker and will not run in CI environment"
    )
    def test_recommendation_experimental(
        self,
        app,
        client,
        db_session,
        results,
        sessions,
       mock_request_experimental_recommender_system,
    ):
        """Test recommendation from an experimental system"""
        result = client.get(self.URL + "?itemid=test_item&container=recommender")
        data = result.json
        print("DEBUG: Response Data:", json.dumps(data, indent=4))
        

        assert 200 == result.status_code,  f"Unexpected response code: {result.status_code}, Response: {data}"
        assert "body" in data and isinstance(data["body"], dict), f"Invalid response format: {data}"
        assert len(data["body"]) > 0, "Empty recommendation body"
        assert all("docid" in rec and "type" in rec for rec in data["body"].values()), "Missing fields in recommendations"



@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
def test_recommendation_interleaved(
    app,
    client,
    db_session,
    results,
    sessions,
    mock_request_experimental_recommender_system,
    mock_request_base_recommender_system,
):
    """Test recommendation with interleaving enabled"""
    app.config["INTERLEAVE"] = True
    result = client.get("/stella/api/v1/recommendation?itemid=test_item&container=recommender")

    data = result.json
    print("Interleaved Response Debug:", json.dumps(data, indent=4))
    assert 200 == result.status_code
    # Given the randomness of the interleaving, we can only check for the keys
    assert "body" in data and isinstance(data["body"], dict), f"Invalid response format: {data}"
    assert len(data["body"]) > 0, "Empty recommendation body"
    assert all("docid" in rec and "type" in rec for rec in data["body"].values()), "Missing fields in recommendations"


class TestPostRecommendationFeedback:
    URL = "/stella/api/v1/recommendation/{}/feedback"

    def test_post_feedback(self, client, results, sessions):
        """Test posting feedback for a recommendation"""
        feedbacks = create_feedbacks(sessions)
        data = {
            "clicks": feedbacks["recommender_base"].clicks,
        }
        result = client.post(self.URL.format(results["recommender"].id), data=data)
        assert 201 == result.status_code

    def test_post_feedback_wrong_id(self, client, results, sessions):
        """Test posting feedback for an invalid recommendation ID"""
        feedbacks = create_feedbacks(sessions)
        data = {
            "clicks": feedbacks["recommender_base"].clicks,
        }
        result = client.post(self.URL.format("999"), data=data)
        assert 404 == result.status_code
