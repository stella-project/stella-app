import requests as req
import json
import random
import time
import datetime

PORT = '8080'
API = 'http://0.0.0.0:' + PORT + '/stella/api/v1'
QUERY = 'study'
QID = 1


def str_time_prop(start, end, format, prop):
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


def random_date(start, end, prop):
    return str_time_prop(start, end, "%Y-%m-%d %H:%M:%S", prop)


def main():

    click_dict = {
        "1": {"docid": "doc1", "clicked": False, "date": None, "system": "EXP"},
        "2": {"docid": "doc14", "clicked": False, "date": None, "system": "BASE"},
        "3": {"docid": "doc2", "clicked": False, "date": None, "system": "EXP"},
        "4": {"docid": "doc14", "clicked": False, "date": None, "system": "BASE"},
        "5": {"docid": "doc3", "clicked": False, "date": None, "system": "EXP"},
        "6": {"docid": "doc13", "clicked": False, "date": None, "system": "BASE"},
        "7": {"docid": "doc4", "clicked": False, "date": None, "system": "EXP"},
        "8": {"docid": "doc14", "clicked": False, "date": None, "system": "BASE"},
        "9": {"docid": "doc5", "clicked": False, "date": None, "system": "EXP"},
        "10": {"docid": "doc15", "clicked": False, "date": None, "system": "BASE"}
    }

    serp_entries = 10
    num_clicks = random.randint(1, serp_entries)
    rank_clicks = random.sample(range(1, serp_entries + 1), num_clicks)

    session_start = random_date("2020-01-01 00:00:00", "2020-12-31 00:00:00", random.random())
    session_start_date = datetime.datetime.strptime(session_start, "%Y-%m-%d %H:%M:%S")
    session_end_date = session_start_date + datetime.timedelta(0, random.randint(10, 3000))

    for click in rank_clicks:
        click_time_str = random_date(session_start,
                                     session_end_date.strftime("%Y-%m-%d %H:%M:%S"),
                                     random.random())
        click_time = datetime.datetime.strptime(click_time_str, "%Y-%m-%d %H:%M:%S")
        tmp = click_dict.get(str(click))
        tmp['clicked'] = True
        tmp['date'] = click_time_str
        click_dict[click] = tmp

    # POST results
    payload = {
        'interleave': True,
        'clicks': json.dumps(click_dict)
    }

    r = req.post(API + '/recommendation/' + str(QID) + '/feedback', data=payload)
    print(r.text)


if __name__ == '__main__':
    main()
