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

    def test_ranking_interleaved(
        self,
        app,
        client,
        db_session,
        results,
        sessions,
        mock_request_system,
        mock_request_base_system,
    ):
        """Test interleaved ranking with custom hits path in the experimental system"""
        app.config["INTERLEAVE"] = True
        query_params = {"query": "Test Query"}
        result = client.get("/stella/api/v1/ranking", query_string=query_params)

        data = result.json
        assert 200 == result.status_code
        # Assert that the structure follows the default STELLA response structure because the baseline system is default
        assert set(data.keys()) == {"header", "body"}
        assert set(data["header"].keys()) == {
            "container",
            "hits",
            "page",
            "q",
            "rid",
            "rpp",
            "sid",
        }
        for key, item in data["body"].items():
            assert list(item.keys()) == ["docid", "type"]

        # Assert we have interleaved results
        assert len(data["body"].items()) == 10
        assert len(data["header"]["container"].keys()) == 2

        for key, item in data["body"].items():
            if item["type"] == "BASE":
                assert item["docid"] in [
                    "doc1",
                    "doc2",
                    "doc3",
                    "doc4",
                    "doc5",
                    "doc6",
                    "doc7",
                    "doc8",
                    "doc9",
                    "doc10",
                ]
            elif item["type"] == "EXP":
                assert item["docid"] in [
                    "10014322236",
                    "10014446027",
                    "10012813890",
                    "10014564344",
                    "10001423122",
                    "10014505904",
                    "10014445127",
                    "10014549633",
                    "10014549634",
                    "10014575867",
                ]


class TestRankingProxy:
    URL = "/stella/api/v1/ranking/proxy"

    def test_ranking_proxy(
        self,
        mock_request_proxy_system,
        client,
        results,
        sessions,
    ):
        """Test the ranking endpoint with a randomly sampled system. Since the database is empty it will always return the only experimental system"""
        query_params = "{'fulltext': 'true', 'spellcheck': 'true', 'hl': 'on', 'q': 'subject:\"Literature review\"'}"

        result = client.get(self.URL, query_string=query_params)
        data = result.json

        assert 200 == result.status_code
        assert "hits" in data
        assert data["hits"].keys() == {"hits", "max_score", "total"}

        response = create_return_experimental()
        assert data == response

    def test_ranking_proxy_fixed_container(
        self,
        mock_request_proxy_system,
        client,
        results,
        sessions,
    ):
        """Test the ranking endpoint with a specified system."""
        query_params = "{'fulltext': 'true', 'spellcheck': 'true', 'hl': 'on', 'q': 'subject:\"Literature review\", 'container': 'ranker_base'}"
        result = client.get(self.URL, query_string=query_params)
        data = result.json

        assert 200 == result.status_code
        assert "hits" in data
        assert data["hits"].keys() == {"hits", "max_score", "total"}

        response = create_return_experimental()
        assert data == response

    def test_ranking_proxy_interleaved(
        self,
        app,
        client,
        db_session,
        results,
        sessions,
        mock_request_proxy_system,
        mock_request_proxy_base_system,
    ):
        """Test interleaved ranking with custom hits path in the experimental system"""
        app.config["INTERLEAVE"] = True
        query_params = "{'fulltext': 'true', 'spellcheck': 'true', 'hl': 'on', 'q': 'subject:\"Literature review\"'}"
        result = client.get(self.URL, query_string=query_params)

        data = result.json
        assert 200 == result.status_code
        # Assert that the structure follows the default STELLA response structure because the baseline system is default
        assert set(data.keys()) == {"header", "body"}
        assert set(data["header"].keys()) == {
            "container",
            "hits",
            "page",
            "q",
            "rid",
            "rpp",
            "sid",
        }
        for key, item in data["body"].items():
            assert list(item.keys()) == ["docid", "type"]

        # Assert we have interleaved results
        assert len(data["body"].items()) == 10
        assert len(data["header"]["container"].keys()) == 2

        for key, item in data["body"].items():
            if item["type"] == "BASE":
                assert item["docid"] in [
                    "doc1",
                    "doc2",
                    "doc3",
                    "doc4",
                    "doc5",
                    "doc6",
                    "doc7",
                    "doc8",
                    "doc9",
                    "doc10",
                ]
            elif item["type"] == "EXP":
                assert item["docid"] in [
                    "10014322236",
                    "10014446027",
                    "10012813890",
                    "10014564344",
                    "10001423122",
                    "10014505904",
                    "10014445127",
                    "10014549633",
                    "10014549634",
                    "10014575867",
                ]



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
