import asyncio
import time
from datetime import datetime
from typing import Dict, Optional, Union

import aiohttp
from app.models import Result, System
from app.services.interleave_service import interleave_rankings
from flask import current_app
from pytz import timezone
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select

tz = timezone("Europe/Berlin")


async def request_results_from_container(
    session: aiohttp.ClientSession,
    container_name: str,
    query: str,
    rpp: int,
    page: int,
    system_type: str = "ranking",
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

    assert system_type in ["ranking", "recommendation"], "Invalid system type"

    query_key = "item_id" if system_type == "recommendation" else "query"
    async with session:
        content = await session.get(
            f"http://{container_name}:5000/{system_type}",
            params={query_key: query, "rpp": rpp, "page": page},
        )
        assert content.status == 200, f"Error: {content.status}"
        return await content.json()


def extract_hits(
    result: Dict, container_name: str, system_role: str
) -> Union[Dict, list]:
    """Extract the results from the system response. This is used to allow dynamic responds schemas.
    This is used for both ranking and recommendation systems.

    Args:
        result (Dict): Results from the requested system container.
        container_name (str): Name of the container results are requested from.
        system_role (str): Role of the system (EXP or BASE).

    Returns:
        Union[Dict, list]: The extracted item dicts in the standardized stella format is returned and the hits list as in the original response.
    """

    # How docids are referenced in the result
    docid_key = current_app.config["SYSTEMS_CONFIG"][container_name].get(
        "docid", "docid"
    )
    hits_path = current_app.config["SYSTEMS_CONFIG"][container_name].get("hits_path")
    current_app.logger.debug(f"Extracting hits from {container_name}: {hits_path}")
    if hits_path is None:
        current_app.logger.debug("No custom hits path provided")
        hits = result["itemlist"]
        current_app.logger.debug(hits)

    else:
        hits = hits_path.find(result)[0].value

    if isinstance(hits[0], dict):  # Custom format
        item_dict = {
            i + 1: {"docid": hits[i][docid_key], "type": system_role}
            for i in range(0, len(hits))
        }
    else:  # Stella fromat
        item_dict = {
            i + 1: {"docid": hits[i], "type": system_role} for i in range(0, len(hits))
        }
    return item_dict, hits  # formatted, original


async def query_system(
    container_name: str,
    query: str,
    rpp: int,
    page: int,
    session_id: int,
    system_role: str = "EXP",
    system_type: str = "ranking",
) -> Union[Result, Dict]:
    """Handle the requesting of a system container. This function increments the request counter for the system, gets the results from the container, extracts the hits, and saves the results to the database.

    Args:
        container_name (str): Name of the container results are requested from.
        query (str): Query string or item id for which results are requested.
        rpp (int): Results Per Page (rpp).
        page (int): Page ID for pagination.
        session_id (int): If of the session this request takes place in.
        system_role (str, optional): Role of the system in the experiment. Either EXP or BASE. Defaults to "EXP".
        system_type (str, optional): Type of the system (ranking or recommendation). Defaults to "ranking".

    Returns:
        Union[Result, Dict]: Result object and the original results from the container.
    """
    current_app.logger.debug(f'Produce ranking with system: "{container_name}"')

    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()

    # Get system ID and check for HEAD request
    # increase number of request counter before actual request, in case of a failure
    database_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if current_app.config["TESTING"]:
        database_uri = database_uri.replace("sqlite:///", "sqlite+aiosqlite:///")
    else:
        database_uri = database_uri.replace("postgresql", "postgresql+asyncpg")
    async_engine = create_async_engine(database_uri)
    AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        system = (
            await session.execute(select(System).where(System.name == container_name))
        ).scalar()

        if query in current_app.config["HEAD_QUERIES"]:
            system.num_requests += 1
        else:
            system.num_requests_no_head += 1
        await session.commit()

    # Get the results from the container
    async with aiohttp.ClientSession() as session:
        result = await request_results_from_container(
            session, container_name, query, rpp, page, system_type=system_type
        )

    item_dict, hits = extract_hits(result, container_name, system_role)

    # calc query execution time in ms
    ts_end = time.time()
    q_time = round((ts_end - ts_start) * 1000)

    # Save the ranking to the database
    async with AsyncSessionLocal() as session:
        system_id = (
            await session.execute(select(System).where(System.name == container_name))
        ).scalar()

        ranking = Result(
            session_id=session_id,
            system_id=system_id.id,
            type=system_role,
            q=query,
            q_date=q_date,
            q_time=q_time,
            num_found=len(hits),
            page=page,
            rpp=rpp,
            items=item_dict,
        )

        session.add(ranking)
        await session.commit()

    return ranking, result


def build_response(
    ranking: Result,
    container_name: str,
    interleaved_ranking: Optional[Result] = None,
    ranking_base: Optional[Result] = None,
    container_name_base: Optional[str] = None,
    result: Optional[Dict] = None,
    result_base: Optional[Dict] = None,
):
    """Function to build the response from the experimental systems.

    Args:
        ranking (Result): Ranking from the requested system. If only this is provided, hence only one system is requested, this is treated as the experimental responds.
        container_name (str): Name of the container the ranking corresponds to.
        interleaved_ranking (Optional[Result], optional): An interleaved ranking. Defaults to None.
        ranking_base (Optional[Result], optional): Ranking from the requested baseline system. Defaults to None.
        container_name_base (Optional[str], optional): Name of the container the ranking_base corresponds to. Defaults to None.
        result (Optional[Result], optional): Parsed results from the requested experimental system. Defaults to None.
        result_base (Optional[Result], optional): Parsed results from the requested baseline system. Defaults to None.
    """

    def build_id_map(container_name, ranking, result):
        """Build the docid ranking position map to construct passthrough responses from interleaved rankings."""
        hits_path = current_app.config["SYSTEMS_CONFIG"][container_name].get(
            "hits_path"
        )
        docid_name = current_app.config["SYSTEMS_CONFIG"][container_name].get(
            "docid", "docid"
        )
        if hits_path:
            matches = hits_path.find(result)
            assert len(matches) == 1

            id_map = {hit[docid_name]: hit for hit in matches[0].value}
        else:
            id_map = {hit[docid_name]: hit for hit in ranking.items.values()}
        return id_map

    def build_header(ranking_obj, container_names):
        """Helper function to build the response header."""
        return {
            "sid": ranking_obj.session_id,
            "rid": ranking_obj.tdi,
            "q": ranking_obj.q,
            "page": ranking_obj.page,
            "rpp": ranking_obj.rpp,
            "hits": ranking_obj.num_found,
            "container": container_names,
        }

    if not current_app.config["INTERLEAVE"]:
        # Not interleaved
        if current_app.config["SYSTEMS_CONFIG"][container_name].get("hits_path"):
            current_app.logger.debug("Not interleaved, custom returns")
            # custom returns

            return result
        else:
            current_app.logger.debug("Not interleaved, no custom returns")
            # no custom returns
            # TODO: this will always state the system type as EXP even if its a BASE system.
            # This can be a problem for A/B test configurations.
            return {
                "header": build_header(ranking, {"exp": container_name}),
                "body": ranking.items,
            }
    else:
        assert interleaved_ranking is not None, "Interleaved ranking is required"
        # Interleaved
        base_path = current_app.config["SYSTEMS_CONFIG"][container_name_base].get(
            "hits_path"
        )
        if base_path:
            current_app.logger.debug("Interleaved, custom returns")
            # custom returns
            id_map = build_id_map(
                container_name_base,
                ranking_base,
                result_base,
            )
            id_map.update(build_id_map(container_name, ranking, result))
            hits = [id_map[doc["docid"]] for doc in interleaved_ranking.items.values()]

            base_path.update(result_base, hits)
            return result_base
        else:
            current_app.logger.debug("Interleaved, no custom returns")
            container_names = {"exp": container_name, "base": container_name_base}
            return {
                "header": build_header(ranking_base, container_names),
                "body": interleaved_ranking.items,
            }


async def make_ranking(
    container_name: str,
    query: str,
    rpp: int,
    page: str,
    session_id: int,
    system_type: str = "ranking",
):
    """Produce a ranking for the given query and container."""
    # Check cache first
    # ignore session_id for caching because it may not be available
    cache_key = f"ranking:{container_name}:{query}:{rpp}:{page}"
    cached_result = await current_app.cache.get(cache_key)
    if cached_result:
        current_app.logger.debug("Ranking cache hit")
        return cached_result

    if current_app.config["INTERLEAVE"]:
        if system_type == "ranking":
            container_name_base = current_app.config["RANKING_BASELINE_CONTAINER"]
        elif system_type == "recommendation":
            container_name_base = current_app.config["RECOMMENDER_BASELINE_CONTAINER"]
        current_app.logger.debug("Started gathering")

        baseline, experimental = await asyncio.gather(
            query_system(
                container_name_base,
                query,
                rpp,
                page,
                session_id,
                system_role="BASE",
                system_type=system_type,
            ),
            query_system(
                container_name,
                query,
                rpp,
                page,
                session_id,
                system_role="EXP",
                system_type=system_type,
            ),
        )
        ranking_base, result_base = baseline
        ranking, result = experimental

        interleaved_ranking = interleave_rankings(ranking, ranking_base)

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
        ranking, result = await query_system(
            container_name,
            query,
            rpp,
            page,
            session_id,
            system_role="EXP",
            system_type=system_type,
        )
        response = build_response(ranking, container_name, result=result)

    await current_app.cache.set(
        cache_key, response, ttl=current_app.config["SESSION_EXPIRATION"]
    )
    return response
