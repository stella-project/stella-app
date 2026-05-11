import aiohttp
import pytest
from app.models import Result, System
from app.services.proxy_service import (
    forward_request,
    make_results,
    request_results_from_container,
)
from werkzeug.datastructures.structures import MultiDict

from ..create_test_data import STELLA_RETURN_PARAMETER, create_return_experimental


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
            == "custom/path?custom-query=Test Query&custom-rpp=10&custom-page=0"
        )
        assert result.rpp == None
        assert result.system_id == system.id
        for i in range(len(result.items)):
            assert list(result.items[str(i + 1)].keys()) == ["docid", "type"]

    @pytest.mark.asyncio
    async def test_query_system_long_query(
        self, mock_request_custom_system_long_query, sessions, db_session
    ):
        container_name = "ranker"
        query = "a" * (Result.q.property.columns[0].type.length + 1)
        rpp = 10
        page = 0
        result = await forward_request(
            container_name,
            url="custom/path",
            params={"custom-query": query, "custom-rpp": rpp, "custom-page": page},
            session_id=sessions["ranker"].id,
            system_role="EXP",
        )

        result = (
            db_session.query(Result).filter_by(session_id=sessions["ranker"].id).first()
        )

        # sqlite that is used for testing does not enforce length limits
        # we need to compare to the actual length of the query
        assert len(result.q) != len(query)
        assert len(result.q) == Result.q.property.columns[0].type.length
        
        
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
        assert set(result["_stella"].keys()) == STELLA_RETURN_PARAMETER

        result.pop("_stella", None)
        assert result == create_return_experimental()


class TestProxyCacheRegression:
    @pytest.mark.usefixtures("systems")
    def test_proxy_cache_uses_page(
        self, client, aio_mock, sessions, db_session
    ):
        """
        The proxy endpoint looks up cached results by (q, page, session_id). If 'page'
        isn't stored on the initial Result row, cached responses won't be returned
        """
        container_name = "ranker"
        session_id = sessions["ranker"].id
        page = 2
        url_path = "custom/path"

        # `stella-page` is popped and must NOT be forwarded to the container.
        mock_url = (
            "http://ranker:5000/custom/path"
            "?custom-page=0&custom-query=Test Query&custom-rpp=10"
        )
        aio_mock.get(mock_url, payload=create_return_experimental(), repeat=True)

        qs = (
            f"stella-container={container_name}"
            f"&stella-sid={session_id}"
            f"&stella-system-type=ranking"
            f"&stella-page={page}"
            f"&custom-page=0"
            f"&custom-query=Test Query"
            f"&custom-rpp=10"
        )

        # First request stores the Result.
        resp1 = client.get(f"/proxy/{url_path}?{qs}")
        assert resp1.status_code == 200

        data1 = resp1.get_json()
        assert data1 is not None
        assert data1.get("_stella", {}).get("page") == page
        assert data1.get("_stella", {}).get("container", {}).get("exp") == container_name

        data1_no_stella = dict(data1)
        data1_no_stella.pop("_stella", None)
        assert data1_no_stella == create_return_experimental()

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        stored = (
            db_session.query(Result)
            .filter_by(session_id=session_id, page=page)
            .all()
        )
        assert len(stored) == 1

        # Second request should be served from cache and not hit the container again.
        resp2 = client.get(f"/proxy/{url_path}?{qs}")
        assert resp2.status_code == 200

        data2 = resp2.get_json()
        assert data2 is not None
        assert data2.get("_stella", {}).get("page") == page
        assert data2.get("_stella", {}).get("container", {}).get("exp") == container_name

        data2_no_stella = dict(data2)
        data2_no_stella.pop("_stella", None)
        assert data2_no_stella == create_return_experimental()

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        stored = (
            db_session.query(Result)
            .filter_by(session_id=session_id, page=page)
            .all()
        )
        # get_cached_response() creates a new Result record with updated timestamp
        assert len(stored) == 2

        # A different page should NOT share cache and should hit the container again.
        other_page = page + 1
        qs_other_page = (
            f"stella-container={container_name}"
            f"&stella-sid={session_id}"
            f"&stella-system-type=ranking"
            f"&stella-page={other_page}"
            f"&custom-page=0"
            f"&custom-query=Test Query"
            f"&custom-rpp=10"
        )
        resp3 = client.get(f"/proxy/{url_path}?{qs_other_page}")
        assert resp3.status_code == 200

        data3 = resp3.get_json()
        assert data3 is not None
        assert data3.get("_stella", {}).get("page") == other_page
        assert data3.get("_stella", {}).get("container", {}).get("exp") == container_name

        data3_no_stella = dict(data3)
        data3_no_stella.pop("_stella", None)
        assert data3_no_stella == create_return_experimental()

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 2

        stored_other_page = (
            db_session.query(Result)
            .filter_by(session_id=session_id, page=other_page)
            .all()
        )
        assert len(stored_other_page) == 1
