import os
import json

JSON_CONFIG = [
    {"name": "gesis_rec_pyterrier", "type": "recommender", "base": True},
    {"name": "gesis_rec_pyserini", "type": "recommender"},
    {"name": "gesis_rank_pyserini_base", "type": "ranker", "base": True},
    {"name": "gesis_rank_pyserini", "type": "recommender"},
]


def test_load_from_json():
    from config import load_from_json

    os.environ["SYSTEMS_CONFIG"] = json.dumps(JSON_CONFIG)
    parsed_config = load_from_json("SYSTEMS_CONFIG")

    assert parsed_config == JSON_CONFIG
