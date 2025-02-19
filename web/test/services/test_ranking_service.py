from app.models import System, Result
from app.services.ranking_service import (
    request_results_from_container,
    query_system,
    extract_hits,
)
from ..create_test_data import create_return_experimental, create_return_base
import os
import pytest

import aiohttp

running_in_ci = os.getenv("CI") == "true"


@pytest.mark.asyncio
async def test_request_results_from_container_base(mock_request_base_system):
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
async def test_request_results_from_container_exp(mock_request_exp_system):
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
    assert len(response["hits"]["hits"][0]) == 10
    assert response["status"] == 200
    assert response["hits"]["total"] == 199073


def test_extract_hits():
    result = create_return_experimental()
    container_name = "ranker"
    type = "EXP"

    item_dict, hits = extract_hits(result, container_name, type)

    assert len(item_dict) == 10
    assert len(hits) == 10
    assert list(item_dict[1].keys()) == ["docid", "type"]
    assert item_dict[1]["docid"] == "10014322236"


@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
@pytest.mark.asyncio
async def test_query_base_system(mock_request_base_system, sessions, db_session):
    container_name = "ranker_base"
    query = "Test Query"
    rpp = 10
    page = 0
    result = await query_system(
        container_name, query, rpp, page, sessions["ranker_base"].id, type="BASE"
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


@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
@pytest.mark.asyncio
async def test_query_experimental_system(mock_request_exp_system, sessions, db_session):
    container_name = "ranker"
    query = "Test Query"
    rpp = 10
    page = 0
    result = await query_system(
        container_name, query, rpp, page, sessions["ranker"].id, type="EXP"
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
