import json
import time
from datetime import datetime
import asyncio
import httpx

import docker
from app.extensions import cache
from app.models import Result, System
from app.services.interleave_service import interleave_rankings
from flask import current_app
from pytz import timezone

from sqlalchemy.future import select

docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")
tz = timezone("Europe/Berlin")


async def request_results_from_conatiner(container_name, query, rpp, page):
    async with httpx.AsyncClient() as client:
        if current_app.config["DEBUG"]:
            container = docker_client.containers.get(container_name)
            ip_address = container.attrs["NetworkSettings"]["Networks"][
                "stella-app_default"
            ]["IPAddress"]

            content = await client.get(
                "http://" + ip_address + ":5000/ranking",
                params={"query": query, "rpp": rpp, "page": page},
            )

        content = await client.get(
            f"http://{container_name}:5000/ranking",
            params={"query": query, "rpp": rpp, "page": page},
        )

    return content.json()


def extract_hits(result, container_name, type):
    # Extract hits list from result and allow custom fields for docid and hits_path
    docid_name = current_app.config["SYSTEMS_CONFIG"][container_name].get(
        "docid", "docid"
    )
    hits_path = current_app.config["SYSTEMS_CONFIG"][container_name].get("hits_path")

    if hits_path is None:
        hits = result["itemlist"]
    else:
        hits = hits_path.find(result)[0].value

    if isinstance(hits[0], dict):
        item_dict = {
            i + 1: {"docid": hits[i][docid_name], "type": type}
            for i in range(0, len(hits))
        }
    else:
        item_dict = {
            i + 1: {"docid": hits[i], "type": type} for i in range(0, len(hits))
        }

    return item_dict, hits


async def query_system(container_name, query, rpp, page, session_id, type="EXP"):
    """query a system with a given query and return the ranking and the result"""
    current_app.logger.debug(f'Produce ranking with system: "{container_name}"')

    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()

    # increase number of request counter before actual request, in case of a failure
    async_session_factory = current_app.extensions["async_session"]
    async with async_session_factory() as session:
        system = await session.execute(
            select(System).where(System.name == container_name)
        )
        system = system.scalar()
        # system = db.session.query(System).filter_by(name=container_name).first()

        if query in current_app.config["HEAD_QUERIES"]:
            system.num_requests += 1
        else:
            system.num_requests_no_head += 1
        await session.commit()

    result = await request_results_from_conatiner(container_name, query, rpp, page)
    item_dict, hits = extract_hits(result, container_name, type)

    # calc query execution time in ms
    ts_end = time.time()
    q_time = round((ts_end - ts_start) * 1000)

    # Save the ranking to the database
    async with async_session_factory() as session:
        system_id = await session.execute(
            select(System).where(System.name == container_name)
        )
        system_id = system_id.scalar()

    ranking = Result(
        session_id=session_id,
        system_id=system_id.id,
        type="RANK",
        q=query,
        q_date=q_date,
        q_time=q_time,
        num_found=len(hits),
        page=page,
        rpp=rpp,
        items=item_dict,
    )

    async with async_session_factory() as session:
        session.add(ranking)
        await session.commit()

    return ranking, result


def build_response(
    ranking,
    container_name,
    interleaved_ranking=None,
    ranking_base=None,
    container_name_base=None,
    result=None,
    result_base=None,
):
    """Function to build the response object for the ranking. This can handle interleving and passthrough."""

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

    def build_simple_response(ranking_obj):
        """Helper function to build a simple response when no interleaving."""
        container_names = {"exp": container_name}
        return {
            "header": build_header(ranking_obj, container_names),
            "body": ranking_obj.items,
        }

    if not interleaved_ranking:
        if current_app.config["SYSTEMS_CONFIG"][container_name].get("hits_path"):
            return result
        return build_simple_response(ranking)

    # If interleaved_ranking is provided
    id_map = build_id_map(
        current_app.config["RANKING_BASELINE_CONTAINER"], ranking_base, result_base
    )
    id_map.update(build_id_map(container_name, ranking, result))
    hits = [id_map[doc["docid"]] for doc in interleaved_ranking.items.values()]

    base_path = current_app.config["SYSTEMS_CONFIG"][container_name_base].get(
        "hits_path"
    )
    if base_path:
        matches = base_path.find(result_base)
        assert len(matches) == 1
        matches[0].value = hits
        return result_base

    container_names = {"exp": container_name, "base": container_name_base}
    return {
        "header": build_header(ranking_base, container_names),
        "body": hits,
    }


# @cache.memoize(timeout=600)
async def make_ranking(container_name, query, rpp, page, session_id):
    if current_app.config["INTERLEAVE"]:
        current_app.logger.warning("Started gathering")
        baseline, experimental = await asyncio.gather(
            query_system(
                current_app.config["RANKING_BASELINE_CONTAINER"],
                query,
                rpp,
                page,
                session_id,
                type="BASE",
            ),
            query_system(container_name, query, rpp, page, session_id, type="EXP"),
        )
        ranking_base, result_base = baseline
        ranking, result = experimental

        current_app.logger.warning("Gathering done")

        interleaved_ranking = interleave_rankings(ranking, ranking_base)

        response = build_response(
            ranking,
            container_name,
            interleaved_ranking,
            ranking_base,
            current_app.config["RANKING_BASELINE_CONTAINER"],
            result,
            result_base,
        )

    else:
        ranking, result = await query_system(
            container_name, query, rpp, page, session_id, type="EXP"
        )
        response = build_response(ranking, container_name, result=result)

    return response
