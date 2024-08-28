import docker
import json
import time
from datetime import datetime
import requests
from flask import jsonify, request, current_app
from app.models import db, Session, System, Result, Feedback
from app.services.interleave_service import tdi
from app.utils import create_dict_response
from pytz import timezone
from app.services.session_service import create_new_session

client = docker.DockerClient(base_url="unix://var/run/docker.sock")
tz = timezone("Europe/Berlin")


def request_results_from_conatiner(container_name, query, rpp, page):
    """
    Produce container-ranking via rest-call implementation
    Tested: True

    @param container_name:  container name (str)
    @param query:           search query (str)
    @param rpp:             results per page (int)
    @param page:            page number (int)

    @return:                container-ranking (dict)
    """
    if current_app.config["DEBUG"]:
        container = client.containers.get(container_name)
        ip_address = container.attrs["NetworkSettings"]["Networks"][
            "stella-app_default"
        ]["IPAddress"]
        content = requests.get(
            "http://" + ip_address + ":5000/ranking",
            params={"query": query, "rpp": rpp, "page": page},
        ).content
        return json.loads(content)

    content = requests.get(
        f"http://{container_name}:5000/ranking",
        params={"query": query, "rpp": rpp, "page": page},
    ).content
    return json.loads(content)


def request_results_from_conatiner_cmd(container_name, query, rpp, page):
    """
    Produce container-ranking via classical cmd-call (fallback solution, much slower than rest-implementation)

    @param container_name:  container name (str)
    @param query:           search query (str)
    @param rpp:             results per page (int)
    @param page:            page number (int)

    @return:                container-ranking (dict)
    """
    container = client.containers.get(container_name)
    cmd = "python3 /script/ranking {} {} {}".format(query, rpp, page)
    exec_res = container.exec_run(cmd)
    result = json.loads(exec_res.output.decode("utf-8"))
    return result


def query_system(container_name, query, rpp, page, session_id, type="EXP"):
    """
    Produce ranking from experimental system in docker container by the container name

    @param container_name:  container name (str)
    @param query:           search query (str)
    @param rpp:             results per page (int)
    @param page:            page number (int)
    @param session_id:      session_id (int)
    @param type:            ranking type (str 'EXP' or 'BASE')

    @return:                ranking (Result)
    """
    current_app.logger.debug(f'produce ranking with container: "{container_name}"...')
    q_date = datetime.now(tz).replace(tzinfo=None, microsecond=0)
    ts_start = time.time()

    # increase number of request counter before actual request, in case of a failure
    system = db.session.query(System).filter_by(name=container_name).first()
    if query in current_app.config["HEAD_QUERIES"]:
        system.num_requests += 1
    else:
        system.num_requests_no_head += 1
    db.session.commit()

    if current_app.config["REST_QUERY"]:
        result = request_results_from_conatiner(container_name, query, rpp, page)
    else:
        result = request_results_from_conatiner_cmd(container_name, query, rpp, page)

    # calc query execution time in ms
    ts_end = time.time()
    q_time = round((ts_end - ts_start) * 1000)

    # TODO: extract the itemlist from the ranking given the config for the system
    # Get path to hitlist in result from config for system
    
    # extract hits list from result
    
    item_dict = {
        i + 1: {"docid": result["itemlist"][i], "type": type}
        for i in range(0, len(result["itemlist"]))
    }

    ranking = Result(
        session_id=session_id,
        system_id=db.session.query(System).filter_by(name=container_name).first().id,
        type="RANK",
        q=query,
        q_date=q_date,
        q_time=q_time,
        num_found=result["num_found"],
        page=page,
        rpp=rpp,
        items=item_dict,
    )

    db.session.add(ranking)
    db.session.commit()

    # Add the original response of the system to the result object
    # This is currently not saved to the database
    ranking.result = result
    return ranking
