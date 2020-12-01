import requests as req
import json
import random
import datetime

STELLA_APP_API = 'http://0.0.0.0:8080/stella/api/v1/'
NUM = 100


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


def dataset_recommendations(num=10, print_status_code=False):
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


def rankings(num=10, print_status_code=False):
    for _ in range(num):
        query = random.choice(['covid-19 OR sars-cov-2',
                               'influenza',
                               'bioenergy',
                               'animal AND protection',
                               'vegan AND diet',
                               'demenz',
                               'depression',
                               'climate change',
                               'bienensterben',
                               'hiv',
                               'cancer',
                               'borderline',
                               'psychiatrie',
                               'mikroplastik',
                               'cannabis',
                               'schlaf',
                               'klimawandel AND in AND china',
                               'corona AND virus'])

        r = req.get(STELLA_APP_API + "ranking?query=" + query)
        r_json = r.json()
        rank_id = r_json.get('header').get('rid')
        payload = simulate(r_json)
        r_post = req.post(STELLA_APP_API + "ranking/" + str(rank_id) + "/feedback", data=payload)
        if print_status_code:
            print(r_post.status_code)


def main():
    # dataset_recommendations(num=NUM)
    rankings(num=NUM, print_status_code=True)


if __name__ == '__main__':
    main()
