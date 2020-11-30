import unittest
import datetime
import random
import json
import requests

STELLA_APP_API = 'http://0.0.0.0:8080/stella/api/v1/'


def simulate(req_json):
    click_dict = req_json.get('body')
    session_start_date = datetime.datetime.now()
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


class TestApp(unittest.TestCase):
    def test_01_get_recommendation(self):
        req = requests.get(STELLA_APP_API + "recommendation/datasets?itemid=" + itemid)
        self.assertEqual(req.status_code, 200)

    def test_02_post_feedback(self):
        req = requests.get(STELLA_APP_API + "recommendation/datasets?itemid=" + itemid)
        req_json = req.json()
        rec_id = req_json.get('header').get('rid')
        payload = simulate(req_json)
        req = requests.post(STELLA_APP_API + "recommendation/" + str(rec_id) + "/feedback", data=payload)
        self.assertEqual(req.status_code, 201)

    def test_03_get_previous_recommendation(self):
        req_first = requests.get(STELLA_APP_API + "recommendation/datasets?itemid=" + itemid)
        req_first_json = req_first.json()
        rec_id = req_first_json.get('header').get('rid')
        req_second = requests.get(STELLA_APP_API + "recommendation/datasets/" + str(rec_id))
        req_second_json = req_second.json()
        self.assertDictEqual(req_first_json.get('body'), req_second_json.get('items'))
