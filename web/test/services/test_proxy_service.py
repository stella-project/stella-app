import os

import aiohttp
import pytest
from app.models import Result, System
from app.services.interleave_service import interleave_rankings
from app.services.proxy_service import (
    forward_request,
    make_results,
    request_results_from_container,
)
from werkzeug.datastructures.structures import MultiDict

from ..create_test_data import create_return_experimental


class TestRequestResults:
    """Test the request_results_from_container function."""

    @pytest.mark.asyncio
    async def test_request_results_from_container(self, mock_request_custom_system):
        """Test if `request_results_from_container` correctly retrieves and returns API data."""
        container_name = "ranker"
        query = "Test Query"
        rpp = 10
        page = 0

        async with aiohttp.ClientSession() as session:
            response = await request_results_from_container(
                session=session,
                container_name=container_name,
                url="custom/path",
                params={"custom-query": query, "custom-rpp": rpp, "custom-page": page},
            )
        print(response)
        assert response == create_return_experimental()


class TestForwardRequest:
    @pytest.mark.asyncio
    async def test_forward_request(
        self, mock_request_custom_system, sessions, db_session
    ):
        container_name = "ranker"
        query = "Test Query"
        rpp = 10
        page = 0
        result = await forward_request(
            container_name,
            url="custom/path",
            params={"custom-query": query, "custom-rpp": rpp, "custom-page": page},
            session_id=sessions["ranker"].id,
            system_role="EXP",
        )

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        result = (
            db_session.query(Result).filter_by(session_id=sessions["ranker"].id).first()
        )
        assert (
            result.q
            == "custom/path{'custom-query': 'Test Query', 'custom-rpp': 10, 'custom-page': 0}"
        )
        assert result.rpp == None
        assert result.system_id == system.id
        print(result.items)
        for i in range(len(result.items)):
            assert list(result.items[str(i + 1)].keys()) == ["docid", "type"]


class TestMakeResults:
    @pytest.mark.asyncio
    async def test_make_results_ab(
        self, mock_request_custom_system, sessions, db_session
    ):
        query = "Test Query"
        rpp = 10
        page = 0
        container_name = "ranker"
        session_id = sessions["ranker"].id
        url = "custom/path"
        params = MultiDict(
            [("custom-query", query), ("custom-rpp", rpp), ("custom-page", page)]
        )
        system_type = "ranking"

        result = await make_results(
            container_name=container_name,
            session_id=session_id,
            url=url,
            params=params,
            system_type=system_type,
        )

        assert result == create_return_experimental()
