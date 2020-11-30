import requests as req
import json
import random
import datetime
import time

STELLA_APP_API = 'http://0.0.0.0:8080/stella/api/v1/'
NUM=10000


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


def simulate(req_json):
    click_dict = req_json.get('body')
    session_start = random_date("2020-01-01 00:00:00", "2020-12-31 00:00:00", random.random())
    session_start_date = datetime.datetime.strptime(session_start, "%Y-%m-%d %H:%M:%S")
    session_end_date = session_start_date + datetime.timedelta(0, random.randint(10, 3000))
    random_clicks = random.sample(range(1, len(click_dict)), random.randint(1, 3))
    random.sample(range(1, 10), random.randint(1, 9))
    for key, val in click_dict.items():
        if int(key) in random_clicks:
            click_dict.update({key: {'docid': req_json.get('body').get(key).get('docid'),
                                     'type': req_json.get('body').get(key).get('type'),
                                     'clicked': True,
                                     'date': session_start_date.strftime("%Y-%m-%d %H:%M:%S")}})
        else:
            click_dict.update({key: {'docid': req_json.get('body').get(key).get('docid'),
                                     'type': req_json.get('body').get(key).get('type'),
                                     'clicked': False,
                                     'date': None}})

    # have to use json.dumps(click_dict) since requests cannot send dict in dict as payload
    # see also this thread: https://stackoverflow.com/questions/38380086/sending-list-of-dicts-as-value-of-dict-with-requests-post-going-wrong
    # the stella-server will accept string-formatted json as well as conventional json
    return {
        'start': session_start_date.strftime("%Y-%m-%d %H:%M:%S"),
        'end': session_end_date.strftime("%Y-%m-%d %H:%M:%S"),
        'interleave': True,
        'clicks': json.dumps(click_dict)
    }


def dataset_recommendations(num=1000000, print_status_code=False):
    for _ in range(num):
        itemid = random.choice(['gesis-ssoar-1002',
                                'gesis-ssoar-1006',
                                'gesis-ssoar-1066',
                                'gesis-ssoar-1008',
                                'literaturpool-7b4d6755baca016a30a143997ce3c93f',
                                'literaturpool-f9731e199de60f842ecedf8f4e785acb',
                                'literaturpool-6da4169a5f952cdea21c3e2fc036ee66',
                                'gesis-ssoar-58842',
                                'gesis-ssoar-58844',
                                'literaturpool-08beeb79c7d2e3d5d2edbadb9850690b',
                                'literaturpool-1b07bf0159a530443ef9cdf37b87e1c9',
                                'gesis-ssoar-60517',
                                'gesis-ssoar-60518'])

        r = req.get(STELLA_APP_API + "recommendation/datasets?itemid=" + itemid)
        r_json = r.json()
        rec_id = r_json.get('header').get('rid')
        payload = simulate(r_json)
        r_post = req.post(STELLA_APP_API + "recommendation/" + str(rec_id) + "/feedback", data=payload)
        if print_status_code:
            print(r_post.status_code)


def main():
    dataset_recommendations(num=NUM)


if __name__ == '__main__':
    main()
