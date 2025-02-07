import importlib
import config
import os
import json
from app import app


JSON_CONFIG = {
    "recommender_base": {"type": "recommender", "base": True},
    "recommender": {"type": "recommender"},
    "ranker_base": {"type": "ranker", "base": True},
    "ranker": {"type": "ranker", "docid": "id", "hits_path": "$.hits.hits[*]"},
}


def test_load_from_json():
    from config import load_from_json

    os.environ["SYSTEMS_CONFIG"] = json.dumps(JSON_CONFIG)
    parsed_config = load_from_json("SYSTEMS_CONFIG")

    assert parsed_config == JSON_CONFIG


def test_load_conf_json():
    # Change env var and reload the config module that loads the config from the environment variables
    os.environ["SYSTEMS_CONFIG"] = json.dumps(JSON_CONFIG)
    importlib.reload(config)
    importlib.reload(app)

    app_instance = app.create_app()
    print(app_instance.config["SYSTEMS_CONFIG"])
    print(JSON_CONFIG)

    assert app_instance.config["SYSTEMS_CONFIG"] == JSON_CONFIG

    assert app_instance.config["RANKING_CONTAINER_NAMES"] == ["ranker_base", "ranker"]
    assert app_instance.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"] == []
    assert app_instance.config["RANKING_BASELINE_CONTAINER"] == "ranker_base"

    assert app_instance.config["RECOMMENDER_CONTAINER_NAMES"] == [
        "recommender_base",
        "recommender",
    ]
    assert app_instance.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"] == []
    assert app_instance.config["RECOMMENDER_BASELINE_CONTAINER"] == "recommender_base"


def test_load_conf_list():
    # Change env var and reload the config module that loads the config from the environment variables
    os.environ["RECSYS_LIST"] = "gesis_rec_pyterrier gesis_rec_pyserini"
    os.environ["RECSYS_BASE"] = "gesis_rec_pyterrier"
    os.environ["RANKSYS_LIST"] = "gesis_rank_pyserini_base gesis_rank_pyserini"
    os.environ["RANKSYS_BASE"] = "gesis_rank_pyserini_base"

    importlib.reload(config)
    importlib.reload(app)

    app_instance = app.create_app()

    assert app_instance.config["RANKING_CONTAINER_NAMES"] == ["ranker_base", "ranker"]
    assert app_instance.config["RANKING_PRECOMPUTED_CONTAINER_NAMES"] == []
    assert app_instance.config["RANKING_BASELINE_CONTAINER"] == "ranker_base"

    assert app_instance.config["RECOMMENDER_CONTAINER_NAMES"] == [
        "recommender_base",
        "recommender",
    ]
    assert app_instance.config["RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES"] == []
    assert app_instance.config["RECOMMENDER_BASELINE_CONTAINER"] == "recommender_base"
