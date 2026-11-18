import copy

from app.models import System


def test_update_systems_adds_new_ranker_to_ranking_containers(app, client, systems, db_session):
    app.config["SYSTEMS_CONFIG"] = copy.deepcopy(app.config["SYSTEMS_CONFIG"])
    payload = {
        "systems": {
            **{name: {"type": s.type, "status": "LIVE"} for name, s in systems.items()},
            "new_ranker": {"type": "RANK", "status": "LIVE"},
            "new_recommender": {"type": "REC", "status": "LIVE"},
        }
    }

    result = client.post("/stella/api/v1/systems/update", json=payload)

    assert result.status_code == 200
    assert app.config["SYSTEMS_CONFIG"]["new_ranker"] == {"type": "ranker"}
    assert app.config["SYSTEMS_CONFIG"]["new_recommender"] == {"type": "recommender"}
    assert "new_ranker" in app.config["RANKING_CONTAINER_NAMES"]
    assert "new_recommender" in app.config["RECOMMENDER_CONTAINER_NAMES"]
    assert db_session.query(System).filter_by(name="new_ranker").first().type == "RANK"


def test_update_systems_skips_invalid_type(app, client, systems, db_session):
    app.config["SYSTEMS_CONFIG"] = copy.deepcopy(app.config["SYSTEMS_CONFIG"])
    payload = {
        "systems": {
            **{name: {"type": s.type, "status": "LIVE"} for name, s in systems.items()},
            "broken": {"type": "unknown", "status": "LIVE"},
        }
    }

    result = client.post("/stella/api/v1/systems/update", json=payload)

    assert result.status_code == 200
    assert "broken" not in app.config["SYSTEMS_CONFIG"]
    assert db_session.query(System).filter_by(name="broken").first() is None
