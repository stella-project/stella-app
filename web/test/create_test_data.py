import datetime
import json
import random
import time

from app.models import Feedback, Result, Session, System
from app.services.session_service import create_new_session

STELLA_RETURN_PARAMETER = {
    "sid",
    "rid",
    "q",
    "page",
    "rpp",
    "hits",
    "container",
    "body"
}


def random_date(start, end, prop, format="%Y-%m-%d %H:%M:%S"):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    source: https://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))
    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def create_systems():
    returns = {}
    returns["ranker_base"] = System(
        name="ranker_base",
        type="RANK",
        system_type="LIVE",
        num_requests=0,
        num_requests_no_head=0,
    )

    returns["ranker"] = System(
        name="ranker",
        type="RANK",
        system_type="LIVE",
        num_requests=0,
        num_requests_no_head=0,
    )

    returns["recommender_base"] = System(
        name="recommender_base",
        type="REC",
        system_type="LIVE",
        num_requests=0,
        num_requests_no_head=0,
    )

    returns["recommender"] = System(
        name="recommender",
        type="REC",
        system_type="LIVE",
        num_requests=0,
        num_requests_no_head=0,
    )
    return returns


def create_sessions(systems):
    result = {}
    for system in systems.keys():
        if system.startswith("ranker"):
            result[system] = create_new_session(
                container_name=system, sid=None, type="ranker"
            )
        elif system.startswith("recommender"):
            result[system] = create_new_session(
                container_name=system, sid=None, type="recommendation"
            )
    return result


def create_return_base():
    page = 0
    rpp = 10
    query = "Test Query"
    itemlist = [
        "doc1",
        "doc2",
        "doc3",
        "doc4",
        "doc5",
        "doc6",
        "doc7",
        "doc8",
        "doc9",
        "doc10",
    ]

    data = {
        "page": page,
        "rpp": rpp,
        "query": query,
        "itemlist": itemlist,
        "num_found": len(itemlist),
    }
    return data


def create_return_recommendation_base():
    page = 0
    rpp = 10
    itemlist = [
        "doc1",
        "doc2",
        "doc3",
        "doc4",
        "doc5",
        "doc6",
        "doc7",
        "doc8",
        "doc9",
        "doc10",
    ]

    data = {
        "page": page,
        "rpp": rpp,
        "itemlist": itemlist,
        "num_found": len(itemlist),
        "itemid": "test_item",
    }
    return data


def create_return_experimental():
    return {
        "hits": {
            "hits": [
                {"id": "10014322236", "type": "article", "_score": 6.751302},
                {"id": "10014446027", "type": "book", "_score": 6.751302},
                {"id": "10012813890", "type": "book", "_score": 6.589573},
                {"id": "10014564344", "type": "article", "_score": 5.7939076},
                {"id": "10001423122", "type": "journal", "_score": 5.7764525},
                {"id": "10014505904", "type": "article", "_score": 5.6911764},
                {"id": "10014445127", "type": "book", "_score": 5.5197597},
                {"id": "10014549633", "type": "book", "_score": 5.5197597},
                {"id": "10014549634", "type": "book", "_score": 5.5197597},
                {"id": "10014575867", "type": "book", "_score": 5.5196695},
            ],
            "max_score": 6.751302,
            "total": 199073,
        },
        "status": 200,
    }


def create_return_recommendation_experimental():
    """Generate a test recommendation response for experimental system (recommender)."""
    return {
        "hits": {
            "hits": [
                {"id": "10014322236", "type": "article", "_score": 6.751302},
                {"id": "10014446027", "type": "book", "_score": 6.751302},
                {"id": "10012813890", "type": "book", "_score": 6.589573},
                {"id": "10014564344", "type": "article", "_score": 5.7939076},
                {"id": "10001423122", "type": "journal", "_score": 5.7764525},
                {"id": "10014505904", "type": "article", "_score": 5.6911764},
                {"id": "10014445127", "type": "book", "_score": 5.5197597},
                {"id": "10014549633", "type": "book", "_score": 5.5197597},
                {"id": "10014549634", "type": "book", "_score": 5.5197597},
                {"id": "10014575867", "type": "book", "_score": 5.5196695},
            ],
            "max_score": 6.751302,
            "total": 199073,
        },
        "status": 200,
    }


def create_results(sessions):
    result_objs = {}
    for system, session in sessions.items():
        if system.startswith("ranker"):
            result_objs[system] = Result(
                session_id=session.id,
                system_id=session.system_ranking,
                type="RANK",
                q="test",
                q_date=session.start,
                q_time=300,
                num_found=10,
                page=0,
                rpp=10,
            )

            if system == "ranker_base":
                result_objs[system].items = json.dumps(
                    {
                        "1": "doc1",
                        "2": "doc2",
                        "3": "doc3",
                        "4": "doc4",
                        "5": "doc5",
                        "6": "doc6",
                        "7": "doc7",
                        "8": "doc8",
                        "9": "doc9",
                        "10": "doc10",
                    }
                )

            elif system == "ranker":
                result_objs[system].items = json.dumps(
                    {
                        "1": "10014322236",
                        "2": "10014446027",
                        "3": "10012813890",
                        "4": "10014564344",
                        "5": "10001423122",
                        "6": "10014505904",
                        "7": "10014445127",
                        "8": "10014549633",
                        "9": "10014549634",
                        "10": "10014575867",
                    }
                )
                original_response = create_return_experimental()
                result_objs[system].custom_response = json.dumps(original_response)

        elif system.startswith("recommender"):
            result_objs[system] = Result(
                session_id=session.id,
                system_id=session.system_ranking,
                type="REC",
                q="test_item",
                q_date=session.start,
                q_time=300,
                num_found=10,
                page=0,
                rpp=10,
            )

            itemlist = {
                str(i + 1): {
                    "docid": f"dataset-{i+1}",
                    "type": "dataset",
                    "rank": i + 1,
                }
                for i in range(5)
            }
            itemlist.update(
                {
                    str(i + 6): {
                        "docid": f"publication-{i+1}",
                        "type": "publication",
                        "rank": i + 6,
                    }
                    for i in range(5)
                }
            )
            result_objs[system].items = json.dumps(itemlist)
            if system == "recommender":
                original_response = create_return_recommendation_experimental()
                result_objs[system].custom_response = json.dumps(original_response)
    return result_objs


def create_feedbacks(sessions):
    returns = {}
    results = create_results(sessions)

    for system, session in sessions.items():
        type = "BASE" if system.endswith("base") else "EXP"

        click_dict = json.loads(results[system].items)
        for idx in range(1, 11):
            click_dict[str(idx)] = {
                "docid": click_dict[str(idx)],
                "clicked": False,
                "date": None,
                "type": type,
            }

        serp_entries = 10
        num_clicks = random.randint(1, serp_entries)
        rank_clicks = random.sample(range(1, serp_entries + 1), num_clicks)

        # set session end time
        end_time = session.start + datetime.timedelta(seconds=3000)

        for click in rank_clicks:
            click_time_str = random_date(
                session.start.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                random.random(),
            )
            click_time = datetime.datetime.strptime(click_time_str, "%Y-%m-%d %H:%M:%S")
            tmp = click_dict.get(str(click))
            tmp["clicked"] = True
            tmp["date"] = click_time_str
            click_dict[click] = tmp

        returns[system] = Feedback(
            start=session.start,
            end=end_time,
            session_id=session.id,
            interleave=True,
            clicks=json.dumps(click_dict),
        )

    return returns
