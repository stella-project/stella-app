import asyncio
import datetime
import json
import random

import click
import requests as req

STELLA_APP_API = "http://0.0.0.0:8080/stella/api/v1/"
# STELLA_APP_API = "http://localhost:8080/stella/api/v1/"
NUM = 200


def simulate(req_json):
    click_dict = req_json.get("body")
    session_start_date = datetime.datetime.now()
    session_end_date = session_start_date + datetime.timedelta(
        0, random.randint(10, 3000)
    )
    random_clicks = random.sample(range(1, len(click_dict)), random.randint(1, 3))
    random.sample(range(1, 10), random.randint(1, 9))
    for key, val in click_dict.items():
        if int(key) in random_clicks:
            click_dict.update(
                {
                    key: {
                        "docid": req_json.get("body").get(key).get("docid"),
                        "type": req_json.get("body").get(key).get("type"),
                        "clicked": True,
                        "date": session_start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                }
            )
        else:
            click_dict.update(
                {
                    key: {
                        "docid": req_json.get("body").get(key).get("docid"),
                        "type": req_json.get("body").get(key).get("type"),
                        "clicked": False,
                        "date": None,
                    }
                }
            )

    # have to use json.dumps(click_dict) since requests cannot send dict in dict as payload
    # see also this thread: https://stackoverflow.com/questions/38380086/sending-list-of-dicts-as-value-of-dict-with-requests-post-going-wrong
    # the stella-server will accept string-formatted json as well as conventional json
    return {
        "start": session_start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end": session_end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "interleave": True,
        "clicks": json.dumps(click_dict),
    }


def dataset_recommendations(num=10, print_status_code=False):
    for _ in range(num):
        print(_)
        itemid = random.choice(
            [
                "gesis-ssoar-13114",
                "gesis-ssoar-25443",
                "gesis-ssoar-29019",
                "gesis-ssoar-27895",
                "gesis-ssoar-10285",
                "literaturpool-18b497718faa37525bb643871626f471",
                "literaturpool-9bebd914e3791b47b540a633740afc74",
                "literaturpool-48ff515801f34041d07b030f44a2826f",
                "literaturpool-bc6c672208cee5f9b9859379bb27c892",
                "literaturpool-9d823a7227548b93d9e841143b4ef2e6",
                "csa-ps-201324081",
                "gesis-bib-61872",
                "cews-2-605360",
                "gris-publication-7o7ktgb3iqe0",
            ]
        )
        print(itemid)

        r = req.get(
            STELLA_APP_API
            + "recommendation/datasets?itemid="
            + itemid
            + "&container=gesis_rec_pyterrier"
        )
        r_json = r.json()
        rec_id = r_json.get("header").get("rid")
        payload = simulate(r_json)
        print(payload)
        r_post = req.post(
            STELLA_APP_API + "recommendation/" + str(rec_id) + "/feedback", data=payload
        )
        if print_status_code:
            print(r_post.status_code)


async def ranking_async(num=10, print_status_code=False):
    import aiohttp

    async def fetch_data(session, query, sid):

        url = STELLA_APP_API + f"ranking?query={query}&sid=s{sid}"
        async with session.get(url) as response:
            # await asyncio.sleep(1)  # Simulating a delay
            data = await response.json()
            print(f"Completed task: {url}")
            return data

    tasks = []
    async with aiohttp.ClientSession() as session:
        for idx in range(num):
            query = random.choice(
                [
                    "covid-19 OR sars-cov-2",
                    "influenza",
                    "bioenergy",
                    "animal AND protection",
                    "vegan AND diet",
                    "demenz",
                    "depression",
                    "climate change",
                    "hiv",
                    "cancer",
                    "borderline",
                    "psychiatrie",
                    "cannabis",
                    "schlaf",
                    "klimawandel AND in AND china",
                    "corona AND virus",
                ]
            )
            sid = f"s{idx}"
            tasks.append(fetch_data(session, query, sid))

        results = await asyncio.gather(*tasks)

    for result in results:
        print(result)


def rankings(num=10, print_status_code=False):
    for idx in range(num):
        query = random.choice(
            [
                "covid-19 OR sars-cov-2",
                "influenza",
                "bioenergy",
                "animal AND protection",
                "vegan AND diet",
                "demenz",
                "depression",
                "climate change",
                "hiv",
                "cancer",
                "borderline",
                "psychiatrie",
                "cannabis",
                "schlaf",
                "klimawandel AND in AND china",
                "corona AND virus",
            ]
        )

        r = req.get(STELLA_APP_API + f"ranking?query={query}&sid=s{idx}")
        print(query)
        r_json = r.json()
        rank_id = r_json.get("header").get("rid")
        payload = simulate(r_json)
        r_post = req.post(
            STELLA_APP_API + "ranking/" + str(rank_id) + "/feedback", data=payload
        )
        if print_status_code:
            print(r_post.status_code)


@click.command()
@click.option("--num", default=NUM, help="Number of requests to simulate.")
@click.option("--mode", default="ranking", help="Mode: ranking or recommendation.")
@click.option(
    "--async",
    "_async",
    default=False,
    help="Enable asynchronous processing.",
)
@click.option(
    "-v", is_flag=True, default=True, help="Verbosity flag to print status codes."
)
def main(num, mode, _async, v):
    if mode == "ranking":
        if _async:
            asyncio.run(ranking_async(num=num, print_status_code=v))
        else:
            rankings(num=num, print_status_code=v)
    elif mode == "recommendation":
        if _async:
            print("Asynchronous mode not implemented for recommendations.")
        else:
            dataset_recommendations(num=num, print_status_code=v)
    else:
        print("Invalid mode. Choose 'ranking' or 'recommendation'.")


if __name__ == "__main__":
    main()
