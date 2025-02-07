import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))


def load_as_list(env_var):
    variable_list = []
    if os.environ.get(env_var):
        for list_item in os.environ.get(env_var).split(" "):
            variable_list.append(list_item)

    return variable_list


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-me"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # General settings
    INTERLEAVE = True if os.environ.get("INTERLEAVE") == "True" else False
    REST_QUERY = True
    BULK_INDEX = True if os.environ.get("BULK_INDEX") == "True" else False
    SESSION_EXPIRATION = os.environ.get("SESSION_EXPIRATION") or 6
    SESSION_EXPIRATION = int(SESSION_EXPIRATION)
    INTERVAL_DB_CHECK = os.environ.get("INTERVAL_DB_CHECK") or 3  # seconds
    INTERVAL_DB_CHECK = int(INTERVAL_DB_CHECK)
    DELETE_SENT_SESSION = (
        True if os.environ.get("DELETE_SENT_SESSION") == "True" else False
    )
    SCHEDULER_API_ENABLED = True

    # Stella Server
    STELLA_SERVER_ADDRESS = os.environ.get("STELLA_SERVER_ADDRESS") or "nginx"
    STELLA_SERVER_API = STELLA_SERVER_ADDRESS + "/stella/api/v1"

    STELLA_SERVER_USER = os.environ.get("STELLA_SERVER_USER") or "gesis@stella.org"
    STELLA_SERVER_PASS = os.environ.get("STELLA_SERVER_PASS") or "pass"
    STELLA_SERVER_USERNAME = os.environ.get("STELLA_SERVER_USERNAME") or "GESIS"

    # Load registered systems
    # Ranking
    RANKING_CONTAINER_NAMES = load_as_list("RANKSYS_LIST")  # container_list
    RANKING_PRECOMPUTED_CONTAINER_NAMES = load_as_list(
        "RANKSYS_PRECOM_LIST"
    )  # container_list_recommendation
    RANKING_BASELINE_CONTAINER = os.environ.get("RANKSYS_BASE")

    # Recommendation
    RECOMMENDER_CONTAINER_NAMES = load_as_list(
        "RECSYS_LIST"
    )  # container_list_recommendation
    RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES = load_as_list(
        "RECSYS_PRECOM_LIST"
    )  # container_precom_list_recommendation
    RECOMMENDER_BASELINE_CONTAINER = os.environ.get("RECSYS_BASE")

    # Create container_dict
    RANKING_CONTAINER_DICT = {}
    for container_name in RANKING_CONTAINER_NAMES:
        RANKING_CONTAINER_DICT[container_name] = {"requests": 0}

    RECOMMENDER_CONTAINER_DICT = {}
    for container_name in RECOMMENDER_CONTAINER_NAMES:
        RECOMMENDER_CONTAINER_DICT[container_name] = {"requests": 0}

    # Load head items
    try:
        f_in = open("data/head/items/gesis.txt", "r", encoding="utf-8-sig")
        HEAD_ITEMS = [line.strip("\n") for line in f_in.readlines()]
    except FileNotFoundError:
        HEAD_ITEMS = []
        print("No head items found")

    try:
        f_in = open("data/head/queries/livivo.txt", "r", encoding="utf-8-sig")
        HEAD_QUERIES = [line.strip("\n") for line in f_in.readlines()]
    except FileNotFoundError:
        HEAD_QUERIES = []
        print("No head queries found")

    STELLA_SERVER_TOKEN = ""
    TOKEN_EXPIRATION = datetime.now()


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")

    # Load registered systems
    # Ranking
    RANKING_CONTAINER_NAMES = [
        "livivo_base",
        "livivo_rank_pyterrier",
    ]  # container_list
    RANKING_PRECOMPUTED_CONTAINER_NAMES = ["livivo_rank_pyterrier"]
    RANKING_BASELINE_CONTAINER = "livivo_base"

    # Recommendation
    RECOMMENDER_CONTAINER_NAMES = ["gesis_rec_pyterrier"]
    RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES = ["gesis_rec_precom"]
    RECOMMENDER_BASELINE_CONTAINER = "gesis_rec_pyterrier"


class PostgresConfig(Config):
    DEBUG = False
    POSTGRES_USER = os.environ.get("POSTGRES_USER") or "postgres"
    POSTGRES_PW = os.environ.get("POSTGRES_PW") or "change-me"
    POSTGRES_URL = os.environ.get("POSTGRES_URL") or "db:5432"
    POSTGRES_DB = os.environ.get("POSTGRES_DB") or "postgres"
    SQLALCHEMY_DATABASE_URI = "postgresql://{user}:{pw}@{url}/{db}".format(
        user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL, db=POSTGRES_DB
    )

    JOBS = [
        {
            "id": "update_server",
            "func": 'app.services.cron_service:check_db_sessions',
            "trigger": "interval",
            "seconds": Config.INTERVAL_DB_CHECK,
        }
    ]


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    RANKING_CONTAINER_NAMES = ["ranker_base", "ranker"]
    RANKING_BASELINE_CONTAINER = "ranker_base"

    RECOMMENDER_CONTAINER_NAMES = ["recommender_base", "recommender"]
    RECOMMENDER_BASELINE_CONTAINER = "recommender_base"


config = {"default": DevelopmentConfig, "postgres": PostgresConfig, "test": TestConfig}
