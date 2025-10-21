import asyncio
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientResponseError
from app.models import Result, System, db
from app.services.interleave_service import interleave_rankings
from app.services.result_service import build_response, extract_hits
from flask import current_app
from werkzeug.datastructures.structures import MultiDict


async def request_results_from_container(
    session: aiohttp.ClientSession,
    container_name: str,
    url: str,
    params: str,
) -> dict:
    """Request results from a system docker container. This is used for both ranking and recommendation systems.
    Args:
        session (aiohttp.ClientSession): Concurrent session object.
        container_name (str): Name of the container results are requested from.
        query (str): Query string or item id for which results are requested.
        rpp (int): Results Per Page (rpp).
        page (int): Page ID for pagination.
        system_type (str, optional): Type of the system (ranking or recommendation). Defaults to "ranking".
    Returns:
        dict: Dictionary containing the results from the system.
    """
    current_app.logger.debug(
        f'Start getting results from container: "{container_name}"'
    )

    if current_app.config["SYSTEMS_CONFIG"][container_name].get("url"):
        # Use custom URL if provided in the config
        system_url = current_app.config["SYSTEMS_CONFIG"][container_name]["url"]
    else:
        system_url = f"http://{container_name}:5000"

    url = f"{system_url}/{url}"

    try:

        async with session.get(
            url=url,
            params=params,
            timeout=aiohttp.ClientTimeout(total=3),
        ) as response:
            response.raise_for_status()
            return await response.json()

    except asyncio.TimeoutError:
        current_app.logger.error(
            f'Timeout while trying to reach "{container_name.upper()}"'
        )
    except ClientResponseError as e:
        current_app.logger.error(
            f'Client error with "{container_name.upper()}": {e.status} - {e.message}'
        )
    except ClientError as e:
        current_app.logger.error(
            f'Connection error "{container_name.upper()}": {str(e)}'
        )
    except Exception as e:
        current_app.logger.exception(
            f'Unexpected error "{container_name.upper()}": {str(e)}'
        )

    return {
        "item_id": "query",
        "itemlist": [],
        "num_found": 0,
        "page": "page",
        "rpp": "rpp",
    }  # fallback return


def build_query_string(url: str, params: MultiDict) -> str:
    """Build a query string from a MultiDict of parameters."""
    return url + "?" + "&".join(f"{k}={v}" for k, v in params.items())


async def forward_request(
    container_name: str,
    url: str,
    params: Any,
    session_id: str,
    system_role: str = "EXP",
) -> Any:
    """Equivalent to the query_system function.
    - We do not need to check for headqueries because this is depricated and we do not parse the query for proxying anymore.
    """
    current_app.logger.debug(f'Produce ranking with system: "{container_name}"')

    q_date = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()

    # Get system ID
    # increase number of request counter before actual request, in case of a failure
    database_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if current_app.config["TESTING"]:
        database_uri = database_uri.replace("sqlite:///", "sqlite+aiosqlite:///")
    else:
        database_uri = database_uri.replace("postgresql", "postgresql+asyncpg")
    system = db.session.query(System).where(System.name == container_name).first()
    system.num_requests_no_head += 1
    db.session.commit()

    # Get the results from the container
    async with aiohttp.ClientSession() as session:
        result = await request_results_from_container(
            session, container_name, url, params
        )

    item_dict, hits = extract_hits(result, container_name, system_role)

    # calc query execution time in ms
    ts_end = time.time()
    q_time = round((ts_end - ts_start) * 1000)

    query = build_query_string(url, params)

    # truncate long queries to fit in the database
    query = query[: Result.q.property.columns[0].type.length]
    if len(query) > Result.q.property.columns[0].type.length:
        current_app.logger.warning(
            f"Query truncated to {Result.q.property.columns[0].type.length} characters."
        )

    # Save the ranking to the database
    system_id = db.session.query(System).where(System.name == container_name).first()

    ranking = Result(
        session_id=session_id,
        system_id=system_id.id,
        type=system_role,
        q=query,
        q_date=q_date,
        q_time=q_time,
        num_found=None,
        page=None,
        rpp=None,
        items=item_dict,
    )

    db.session.add(ranking)
    db.session.commit()

    return ranking, result


async def make_results(
    container_name: str,
    session_id: int,
    url: str,
    params: MultiDict,
    system_type: str,
):
    """Produce a ranking for the given query and container."""
    if current_app.config["INTERLEAVE"]:
        if system_type == "ranking":
            container_name_base = current_app.config["RANKING_BASELINE_CONTAINER"]
        elif system_type == "recommendation":
            container_name_base = current_app.config["RECOMMENDER_BASELINE_CONTAINER"]
        current_app.logger.debug("Started gathering")

        baseline, experimental = await asyncio.gather(
            forward_request(
                container_name=container_name_base,
                url=url,
                params=params,
                session_id=session_id,
                system_role="BASE",
            ),
            forward_request(
                container_name=container_name,
                url=url,
                params=params,
                session_id=session_id,
                system_role="EXP",
            ),
        )
        ranking_base, result_base = baseline
        ranking, result = experimental

        interleaved_ranking = interleave_rankings(
            ranking, ranking_base, system_type, rpp=len(ranking_base.items)
        )

        response = build_response(
            ranking=ranking,
            container_name=container_name,
            interleaved_ranking=interleaved_ranking,
            ranking_base=ranking_base,
            container_name_base=container_name_base,
            result=result,
            result_base=result_base,
        )

    else:
        # A/B testing
        ranking, result = await forward_request(
            container_name=container_name,
            url=url,
            params=params,
            session_id=session_id,
            system_role="EXP",
        )
        response = build_response(ranking, container_name, result=result)
    return response
