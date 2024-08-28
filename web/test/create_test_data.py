# import random
# import time
# from app.models import Session, Feedback, Result
# import datetime
# import json
from app.models import System, Result, Feedback
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


def create_systems(type):
    if type == "ranker":
        ranker_base = System(
            name="ranker_base",
            type="RANK",
            system_type="LIVE",
            num_requests=0,
            num_requests_no_head=0,
        )

        ranker = System(
            name="ranker",
            type="RANK",
            system_type="LIVE",
            num_requests=0,
            num_requests_no_head=0,
        )
        return [ranker_base, ranker]

    elif type == "recommender":
        recommender_base = System(
            name="recommender_base",
            type="REC",
            system_type="LIVE",
            num_requests=0,
            num_requests_no_head=0,
        )

        recommender = System(
            name="recommender",
            type="REC",
            system_type="LIVE",
            num_requests=0,
            num_requests_no_head=0,
        )
        return [recommender_base, recommender]


def create_result(session, type):
    type_db = "RANK" if type == "ranker" else "REC"
    system_id = (
        session[type].system_ranking
        if type == "ranker"
        else session[type].system_recommendation
    )
    return Result(
        session_id=session[type].id,
        system_id=system_id,
        type=type_db,
        q="test",
        q_date=session[type].start,
        q_time=300,
        num_found=10,
        page=0,
        rpp=20,
        items=json.dumps(
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
        ),
    )


def create_feedback(number_of_feedbacks, sessions, type="ranker"):
    generated_feedbacks = []
    for _ in range(0, number_of_feedbacks):
        click_dict = {
            "1": {"docid": "doc1", "clicked": False, "date": None, "type": "EXP"},
            "2": {"docid": "doc14", "clicked": False, "date": None, "type": "BASE"},
            "3": {"docid": "doc2", "clicked": False, "date": None, "type": "EXP"},
            "4": {"docid": "doc14", "clicked": False, "date": None, "type": "BASE"},
            "5": {"docid": "doc3", "clicked": False, "date": None, "type": "EXP"},
            "6": {"docid": "doc13", "clicked": False, "date": None, "type": "BASE"},
            "7": {"docid": "doc4", "clicked": False, "date": None, "type": "EXP"},
            "8": {"docid": "doc14", "clicked": False, "date": None, "type": "BASE"},
            "9": {"docid": "doc5", "clicked": False, "date": None, "type": "EXP"},
            "10": {"docid": "doc15", "clicked": False, "date": None, "type": "BASE"},
        }

        serp_entries = 10
        num_clicks = random.randint(1, serp_entries)
        rank_clicks = random.sample(range(1, serp_entries + 1), num_clicks)

        # set session end time
        end_time = sessions[type].start + datetime.timedelta(seconds=3000)

        for click in rank_clicks:
            click_time_str = random_date(
                sessions[type].start.strftime("%Y-%m-%d %H:%M:%S"),
                end_time.strftime("%Y-%m-%d %H:%M:%S"),
                random.random(),
            )
            click_time = datetime.datetime.strptime(click_time_str, "%Y-%m-%d %H:%M:%S")
            tmp = click_dict.get(str(click))
            tmp["clicked"] = True
            tmp["date"] = click_time_str
            click_dict[click] = tmp

        generated_feedbacks.append(
            Feedback(
                start=sessions[type].start,
                end=end_time,
                session_id=sessions[type].id,
                interleave=True,
                clicks=json.dumps(click_dict),
            )
        )
        return generated_feedbacks


def create_experimental_return():
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


# TODO: experimental test response