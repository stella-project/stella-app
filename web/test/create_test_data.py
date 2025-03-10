# import random
# import time
# from app.models import Session, Feedback, Result
# import datetime
# import json
from app.models import System, Result, Feedback, Session
from app.services.session_service import create_new_session

import datetime
import random
import json
import time


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
                container_name=system, sid=None, type="recommender"
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


def create_return_experimental():
    return {
        "hits": {
            "hits": [
                [
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
                ]
            ],
            "max_score": 6.751302,
            "total": 199073,
        },
        "status": 200,
    }

def create_results(sessions):
    result_objs = {}

    for system, session in sessions.items():
        # Handle Ranker Systems
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
                    {str(i): f"doc{i}" for i in range(1, 11)}
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

        # Handle Recommender Systems
        elif system.startswith("recommender"):
            result_objs[system] = Result(
                session_id=session.id,
                system_id=session.system_recommendation,
                type="REC",
                q="test_item",
                q_date=session.start,
                q_time=300,
                num_found=7,
                page=0,
                rpp=10,
                items=json.dumps({str(i): f"dataset{i}" for i in range(1, 5)}),  # Mock dataset
            )

        # Ensure recommender_base is added properly
        if system == "recommender_base":
            result_objs["recommender_base"] = Result(
                session_id=session.id,
                system_id=session.system_recommendation,
                type="REC",
                q="test_item",
                q_date=session.start,
                q_time=300,
                num_found=7,
                page=0,
                rpp=10,
                items=json.dumps({str(i): f"dataset{i}" for i in range(1, 5)}),  # Mock dataset
            )

    return result_objs
def create_feedbacks(sessions):
    returns = {}

    results = create_results(sessions)

    for system, session in sessions.items():
        type = "BASE" if system.endswith("base") else "EXP"

        click_dict = json.loads(results[system].items)

        # Ensure all expected items exist in click_dict
        for idx in range(1, 11):
            key = str(idx)
            if key not in click_dict:
                click_dict[key] = {"docid": f"missing_doc{idx}", "clicked": False, "date": None, "type": type}
            else:
                click_dict[key] = {
                    "docid": click_dict[key],  # Ensure it’s correctly structured
                    "clicked": False,
                    "date": None,
                    "type": type,
                }

        # Set session end time
        end_time = session.start + datetime.timedelta(seconds=3000)

        # Fix: Convert keys to list before sampling
        click_keys = list(click_dict.keys())
        num_clicks = min(len(click_keys), random.randint(1, 10))  # Avoid exceeding available items
        rank_clicks = random.sample(click_keys, num_clicks)

        for click in rank_clicks:
            click_time_str = random_date(
                session.start.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                random.random(),
            )
            click_dict[click]["clicked"] = True
            click_dict[click]["date"] = click_time_str

        returns[system] = Feedback(
            start=session.start,
            end=end_time,
            session_id=session.id,
            interleave=True,
            clicks=json.dumps(click_dict),
        )

    return returns



def create_return_recommendation():
    return {
        "body": {
            "datasets": [{"id": "123", "title": "Mock Dataset"}],
            "publications": [{"id": "456", "title": "Mock Publication"}]
        },
        "header": {
            "container": {"exp": "recommender"},
            "itemid": "test_item",
            "rid": 5,
            "sid": "some-session-id"
        }
    }