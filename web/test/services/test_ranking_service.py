import os

import aiohttp
import pytest
from app.models import Result, System
from app.services.interleave_service import interleave_rankings
from app.services.ranking_service import (
    build_response,
    extract_hits,
    query_system,
    request_results_from_container,
)

from ..create_test_data import (
    create_return_base,
    create_return_experimental,
    create_return_recommendation_base,
    create_return_recommendation_experimental,
)

running_in_ci = os.getenv("CI") == "true"


class TestRequestResults:
    """Test the request_results_from_container function."""

    @pytest.mark.asyncio
    async def test_request_results_from_container_base(self, mock_request_base_system):
        """Test if `request_results_from_container` correctly retrieves and returns API data."""
        container_name = "ranker_base"
        query = "Test Query"
        rpp = 10
        page = 0

        async with aiohttp.ClientSession() as session:
            response = await request_results_from_container(
                session=session,
                container_name=container_name,
                query=query,
                rpp=rpp,
                page=page,
            )

        assert response == create_return_base()
        assert response["num_found"] == 10
        assert len(response["itemlist"]) == 10
        assert response["query"] == query
        assert response["page"] == page
        assert response["rpp"] == rpp

    @pytest.mark.asyncio
    async def test_request_results_from_container_base_rec(
        self, mock_request_base_recommender
    ):
        """Test if `request_results_from_container` correctly retrieves and returns API data."""
        container_name = "recommender_base"
        query = "test_item"
        rpp = 10
        page = 0

        async with aiohttp.ClientSession() as session:
            response = await request_results_from_container(
                session=session,
                container_name=container_name,
                query=query,
                rpp=rpp,
                page=page,
                system_type="recommendation",
            )
        assert response == create_return_recommendation_base()
        assert response["num_found"] == 10
        assert len(response["itemlist"]) == 10
        assert response["item_id"] == query
        assert response["page"] == page
        assert response["rpp"] == rpp

    @pytest.mark.asyncio
    async def test_request_results_from_container_exp(self, mock_request_system):
        """Test if `request_results_from_container` correctly retrieves and returns API data."""
        container_name = "ranker"
        query = "Test Query"
        rpp = 10
        page = 0

        async with aiohttp.ClientSession() as session:
            response = await request_results_from_container(
                session=session,
                container_name=container_name,
                query=query,
                rpp=rpp,
                page=page,
            )

        assert response == create_return_experimental()
        assert len(response["hits"]["hits"]) == 10
        assert response["status"] == 200
        assert response["hits"]["total"] == 199073

    @pytest.mark.asyncio
    async def test_request_results_from_container_exp_rec(
        self, mock_request_recommender
    ):
        """Test if `request_results_from_container` correctly retrieves and returns API data."""
        container_name = "recommender"
        query = "test_item"
        rpp = 10
        page = 0

        async with aiohttp.ClientSession() as session:
            response = await request_results_from_container(
                session=session,
                container_name=container_name,
                query=query,
                rpp=rpp,
                page=page,
                system_type="recommendation",
            )
        assert response == create_return_experimental()
        assert len(response["hits"]["hits"]) == 10
        assert response["status"] == 200
        assert response["hits"]["total"] == 199073


class TestExtractHits:
    def test_extract_hits(self):
        result = create_return_base()
        item_dict, hits = extract_hits(
            result, container_name="ranker_base", system_role="BASE"
        )

        assert len(item_dict) == 10
        assert len(hits) == 10
        assert list(item_dict[1].keys()) == ["docid", "type"]
        assert item_dict[1]["docid"] == "doc1"

    def test_extract_hits_rec(self):
        result = create_return_recommendation_base()
        item_dict, hits = extract_hits(
            result, container_name="recommender_base", system_role="BASE"
        )

        assert len(item_dict) == 10
        assert len(hits) == 10
        assert list(item_dict[1].keys()) == ["docid", "type"]
        assert item_dict[1]["docid"] == "doc1"

    def test_extract_hits_exp(self):
        """custom response"""
        result = create_return_experimental()
        item_dict, hits = extract_hits(
            result, container_name="ranker", system_role="EXP"
        )

        assert len(item_dict) == 10
        assert len(hits) == 10
        assert list(item_dict[1].keys()) == ["docid", "type"]
        assert item_dict[1]["docid"] == "10014322236"

    def test_extract_hits_rec_exp(self):
        """custom response"""
        result = create_return_recommendation_experimental()
        item_dict, hits = extract_hits(
            result, container_name="recommender", system_role="EXP"
        )

        assert len(item_dict) == 10
        assert len(hits) == 10
        assert list(item_dict[1].keys()) == ["docid", "type"]
        assert item_dict[1]["docid"] == "10014322236"


class TestQuerySystem:
    @pytest.mark.asyncio
    async def test_query_base_system(
        self, mock_request_base_system, sessions, db_session
    ):
        container_name = "ranker_base"
        query = "Test Query"
        rpp = 10
        page = 0
        result = await query_system(
            container_name,
            query,
            rpp,
            page,
            sessions["ranker_base"].id,
            system_role="BASE",
        )

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        result = (
            db_session.query(Result)
            .filter_by(session_id=sessions["ranker_base"].id)
            .first()
        )
        assert result.q == query
        assert result.rpp == rpp
        assert result.system_id == system.id
        for i in range(len(result.items)):
            assert list(result.items[str(i + 1)].keys()) == ["docid", "type"]

    @pytest.mark.asyncio
    async def test_query_base_system_rec(
        self, mock_request_base_recommender, sessions, db_session
    ):
        container_name = "recommender_base"
        query = "test_item"
        rpp = 10
        page = 0
        result = await query_system(
            container_name,
            query,
            rpp,
            page,
            sessions[container_name].id,
            system_role="BASE",
            system_type="recommendation",
        )

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        result = (
            db_session.query(Result)
            .filter_by(session_id=sessions[container_name].id)
            .first()
        )
        assert result.q == query
        assert result.rpp == rpp
        assert result.system_id == system.id
        for i in range(len(result.items)):
            assert list(result.items[str(i + 1)].keys()) == ["docid", "type"]

    @pytest.mark.skipif(
        running_in_ci, reason="Test requires Docker and will not run in CI environment"
    )
    @pytest.mark.asyncio
    async def test_query_experimental_system(
        self, mock_request_system, sessions, db_session
    ):
        container_name = "ranker"
        query = "Test Query"
        rpp = 10
        page = 0
        result = await query_system(
            container_name, query, rpp, page, sessions["ranker"].id, system_role="EXP"
        )

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        result = (
            db_session.query(Result).filter_by(session_id=sessions["ranker"].id).first()
        )
        assert result.q == query
        assert result.rpp == rpp
        assert result.system_id == system.id
        for i in range(len(result.items)):
            assert list(result.items[str(i + 1)].keys()) == ["docid", "type"]

    @pytest.mark.asyncio
    async def test_query_base_system_rec(
        self, mock_request_recommender, sessions, db_session
    ):
        container_name = "recommender"
        query = "test_item"
        rpp = 10
        page = 0
        result = await query_system(
            container_name,
            query,
            rpp,
            page,
            sessions["recommender"].id,
            system_role="EXP",
            system_type="recommendation",
        )

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        result = (
            db_session.query(Result)
            .filter_by(session_id=sessions["recommender"].id)
            .first()
        )
        assert result.q == query
        assert result.rpp == rpp
        assert result.system_id == system.id
        for i in range(len(result.items)):
            assert list(result.items[str(i + 1)].keys()) == ["docid", "type"]


class TestBuildResponse:
    @pytest.mark.asyncio
    async def test_build_response_interleaved_custom_return(
        self,
        app,
        mock_request_base_system,
        mock_request_system,
        sessions,
        db_session,
    ):
        """Test interleaved ranking with custom hits path in both systems"""
        app.config["INTERLEAVE"] = True

        # experimental system
        ranking_base, result_base = await query_system(
            container_name="ranker",
            query="Test Query",
            rpp=10,
            page=0,
            session_id=sessions["ranker"].id,
            system_role="BASE",
        )
        # experimental system
        ranking, result = await query_system(
            container_name="ranker",
            query="Test Query",
            rpp=10,
            page=0,
            session_id=sessions["ranker"].id,
            system_role="EXP",
        )
        interleaved_ranking = interleave_rankings(ranking, ranking_base)

        response = build_response(
            ranking=ranking,
            container_name="ranker",
            interleaved_ranking=interleaved_ranking,
            ranking_base=ranking_base,
            container_name_base="ranker",
            result=result,
            result_base=result_base,
        )
        assert list(response.keys()) == ["hits", "status"]
        for item in response["hits"]["hits"]:
            assert item["id"] in [
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

    @pytest.mark.asyncio
    async def test_build_response(self, mock_request_base_system, sessions, db_session):
        # not interleaved, base
        ranking, result = await query_system(
            container_name="ranker_base",
            query="Test Query",
            rpp=10,
            page=0,
            session_id=sessions["ranker_base"].id,
            system_role="BASE",
        )
        response = build_response(
            ranking,
            "ranker_base",
        )
        assert response["header"]["q"] == "Test Query"
        assert response["header"]["rpp"] == 10
        for i in range(len(response["body"])):
            assert list(response["body"][i + 1].keys()) == ["docid", "type"]

    @pytest.mark.asyncio
    async def test_build_response_custom_return(
        self, mock_request_system, sessions, db_session
    ):
        # not interleaved, one system, custom response
        ranking, result = await query_system(
            container_name="ranker",
            query="Test Query",
            rpp=10,
            page=0,
            session_id=sessions["ranker"].id,
            system_role="EXP",
        )

        response = build_response(
            ranking=ranking, container_name="ranker", result=result
        )
        assert list(response.keys()) == ["hits", "status"]
        for item in response["hits"]["hits"]:
            assert item["id"] in [
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

    @pytest.mark.asyncio
    async def test_build_response_interleaved_rec(
        self,
        app,
        mock_request_base_recommender,
        mock_request_recommender,
        sessions,
        db_session,
    ):
        app.config["INTERLEAVE"] = True

        ranking_base, result_base = await query_system(
            container_name="recommender_base",
            query="test_item",
            rpp=10,
            page=0,
            session_id=sessions["recommender_base"].id,
            system_role="BASE",
            system_type="recommendation",
        )
        ranking, result = await query_system(
            container_name="recommender_base",
            query="test_item",
            rpp=10,
            page=0,
            session_id=sessions["recommender_base"].id,
            system_role="EXP",
            system_type="recommendation",
        )
        interleaved_ranking = interleave_rankings(ranking, ranking_base)

        response = build_response(
            ranking=ranking,
            container_name="recommender_base",
            interleaved_ranking=interleaved_ranking,
            ranking_base=ranking_base,
            container_name_base="recommender_base",
            result=result,
            result_base=result_base,
        )
        assert response["header"]["q"] == "test_item"
        assert response["header"]["rpp"] == 10
        assert response["header"]["container"]["base"] == "recommender_base"
        assert response["header"]["container"]["exp"] == "recommender_base"

        assert len(response["body"]) == 10

    @pytest.mark.asyncio
    async def test_build_response_interleaved_custom_return_rec(
        self,
        app,
        mock_request_base_recommender,
        mock_request_recommender,
        sessions,
        db_session,
    ):
        app.config["INTERLEAVE"] = True

        ranking_base, result_base = await query_system(
            container_name="recommender",
            query="test_item",
            rpp=10,
            page=0,
            session_id=sessions["recommender"].id,
            system_role="BASE",
            system_type="recommendation",
        )
        ranking, result = await query_system(
            container_name="recommender",
            query="test_item",
            rpp=10,
            page=0,
            session_id=sessions["recommender"].id,
            system_role="EXP",
            system_type="recommendation",
        )
        interleaved_ranking = interleave_rankings(ranking, ranking_base)

        response = build_response(
            ranking=ranking,
            container_name="recommender",
            interleaved_ranking=interleaved_ranking,
            ranking_base=ranking_base,
            container_name_base="recommender",
            result=result,
            result_base=result_base,
        )
        assert list(response.keys()) == ["hits", "status"]
        for item in response["hits"]["hits"]:
            assert item["id"] in [
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

    @pytest.mark.asyncio
    async def test_build_response_rec(
        self, mock_request_base_recommender, sessions, db_session
    ):
        # not interleaved, base
        ranking, result = await query_system(
            container_name="recommender_base",
            query="test_item",
            rpp=10,
            page=0,
            session_id=sessions["recommender_base"].id,
            system_role="BASE",
            system_type="recommendation",
        )
        response = build_response(
            ranking,
            "recommender_base",
        )
        assert response["header"]["q"] == "test_item"
        assert response["header"]["rpp"] == 10
        for i in range(len(response["body"])):
            assert list(response["body"][i + 1].keys()) == ["docid", "type"]

    @pytest.mark.asyncio
    async def test_build_response_custom_return_rec(
        self, mock_request_recommender, sessions, db_session
    ):
        # not interleaved, one system, custom response
        ranking, result = await query_system(
            container_name="recommender",
            query="test_item",
            rpp=10,
            page=0,
            session_id=sessions["recommender"].id,
            system_role="EXP",
            system_type="recommendation",
        )
        response = build_response(
            ranking=ranking, container_name="recommender", result=result
        )
        assert list(response.keys()) == ["hits", "status"]
        for item in response["hits"]["hits"]:
            assert item["id"] in [
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
