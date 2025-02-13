from app.models import System, Result
from app.services.ranking_service import request_results_from_conatiner, query_system
import requests_mock
from ..create_test_data import create_return_experimental, create_return_base
import os
import pytest
import httpx
from unittest import mock

running_in_ci = os.getenv("CI") == "true"

from httpx import Response
import asyncio

@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
@pytest.mark.asyncio
async def test_request_results_from_conatiner(mock_request_base_system):
    container_name = "ranker_base"
    mock_ranking = mock.AsyncMock(name="ranking")
    mock_ranking.get.return_value = mock.AsyncMock(
        json=mock.AsyncMock(return_value=create_return_base())
    )

    with mock.patch(
        "app.services.ranking_service.httpx.AsyncClient", return_value=mock_ranking
    ):
        result = await request_results_from_conatiner(
            container_name=container_name, query="Test Query", rpp=10, page=1
        )
        
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, sync_test)
    assert result == create_return_base()

    # async with httpx.AsyncClient() as client:
    #     route = mock.respx.get("http://ranker_base:5000/")
    #     response = await client.get("http://ranker_base:5000/")

    #     result = await request_results_from_conatiner(
    #         container_name=container_name, query="Test Query", rpp=10, page=1
    #     )

    # # assert result == create_return_base()
    # assert route.called
    # assert response.status_code == 200

    # async with httpx.AsyncClient() as client:
    #     result = await request_results_from_conatiner(
    #         container_name=container_name, query="Test Query", rpp=10, page=1
    #     )
    # data = create_return_base()

    # with patch(
    #     "app.services.ranking_service.httpx.AsyncClient", return_value=mock_http_client
    # ):
    #     # Mock DEBUG mode

    #     # Call the function

    #     mock_http_client.get.assert_any_call(
    #         f"http://{container_name}:5000/ranking",
    #         container_name=container_name,
    #         query="Test Query",
    #         rpp=10,
    #         page=1,
    #     )
    #     # Assertions
    # assert result == create_return_base()


@pytest.mark.skipif(
    running_in_ci, reason="Test requires Docker and will not run in CI environment"
)
def test_query_base_system(mock_request_base_system, sessions, db_session):
    container_name = "ranker_base"
    query = "Test Query"
    rpp = 10
    page = 1
    result = query_system(
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
def test_query_experimental_system(
    mock_request_experimental_system, sessions, db_session
):
    container_name = "ranker"
    query = "Test Query"
    rpp = 10
    page = 1
    result = query_system(
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
