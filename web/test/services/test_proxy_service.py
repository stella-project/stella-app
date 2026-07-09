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
            page=page,
            rpp=rpp,
            system_role="EXP"
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
        assert result.rpp == rpp
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
            page=page,
            rpp=rpp,
            system_role="EXP"
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
            page=page,
            rpp=rpp
        )
        assert set(result["_stella"].keys()) == STELLA_RETURN_PARAMETER

        result.pop("_stella", None)
        assert result == create_return_experimental()


class TestProxyCacheRegression:
    """The proxy endpoint looks up cached results by (q, page, session_id)."""

    @pytest.mark.usefixtures("systems")
    def test_initial_request_persists_result_with_page(
        self, client, aio_mock, sessions, db_session
    ):
        """First request hits the container and stores a Result keyed by page and rpp."""
        container_name = "ranker"
        session_id = sessions["ranker"].id
        page = 2
        rpp = 10
        url_path = "custom/path"

        # `stella-page` and `stella-rpp` are popped and must NOT be forwarded to the container.
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
            f"&stella-rpp={rpp}"
            f"&custom-page=0"
            f"&custom-query=Test Query"
            f"&custom-rpp=10"
        )

        resp = client.get(f"/proxy/{url_path}?{qs}")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data is not None
        assert data.get("_stella", {}).get("page") == page
        assert data.get("_stella", {}).get("rpp") == rpp
        assert data.get("_stella", {}).get("container", {}).get("exp") == container_name

        data_no_stella = dict(data)
        data_no_stella.pop("_stella", None)
        assert data_no_stella == create_return_experimental()

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        stored = (
            db_session.query(Result)
            .filter_by(session_id=session_id, page=page)
            .all()
        )
        assert len(stored) == 1
        assert stored[0].page == page
        assert stored[0].rpp == rpp

    @pytest.mark.usefixtures("systems")
    def test_repeated_request_is_served_from_cache(
        self, client, aio_mock, sessions, db_session
    ):
        """A second identical request reuses the cache and does not hit the container."""
        container_name = "ranker"
        session_id = sessions["ranker"].id
        page = 2
        rpp = 10
        url_path = "custom/path"

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
            f"&stella-rpp={rpp}"
            f"&custom-page=0"
            f"&custom-query=Test Query"
            f"&custom-rpp=10"
        )

        client.get(f"/proxy/{url_path}?{qs}")

        resp = client.get(f"/proxy/{url_path}?{qs}")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data is not None
        assert data.get("_stella", {}).get("page") == page
        assert data.get("_stella", {}).get("container", {}).get("exp") == container_name

        data_no_stella = dict(data)
        data_no_stella.pop("_stella", None)
        assert data_no_stella == create_return_experimental()

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 1

        stored = (
            db_session.query(Result)
            .filter_by(session_id=session_id, page=page)
            .all()
        )
        # get_cached_response() creates a new Result record with updated timestamp
        assert len(stored) == 2

    @pytest.mark.usefixtures("systems")
    def test_different_page_bypasses_cache(
        self, client, aio_mock, sessions, db_session
    ):
        """A request for a different page does not share cache and hits the container again."""
        container_name = "ranker"
        session_id = sessions["ranker"].id
        page = 2
        other_page = page + 1
        rpp = 10
        url_path = "custom/path"

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
            f"&stella-rpp={rpp}"
            f"&custom-page=0"
            f"&custom-query=Test Query"
            f"&custom-rpp=10"
        )

        client.get(f"/proxy/{url_path}?{qs}")

        qs_other_page = (
            f"stella-container={container_name}"
            f"&stella-sid={session_id}"
            f"&stella-system-type=ranking"
            f"&stella-page={other_page}"
            f"&stella-rpp={rpp}"
            f"&custom-page=0"
            f"&custom-query=Test Query"
            f"&custom-rpp=10"
        )

        resp = client.get(f"/proxy/{url_path}?{qs_other_page}")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data is not None
        assert data.get("_stella", {}).get("page") == other_page
        assert data.get("_stella", {}).get("container", {}).get("exp") == container_name

        data_no_stella = dict(data)
        data_no_stella.pop("_stella", None)
        assert data_no_stella == create_return_experimental()

        system = db_session.query(System).filter_by(name=container_name).first()
        assert system.num_requests_no_head == 2

        stored_other_page = (
            db_session.query(Result)
            .filter_by(session_id=session_id, page=other_page)
            .all()
        )
        assert len(stored_other_page) == 1
