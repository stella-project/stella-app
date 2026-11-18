from app.commands import seed_db
from app.extensions import db
from app.models import System

SYSTEM_CONFIG = {
    "RANKING_CONTAINER_NAMES": ["ranker_base", "ranker"],
    "RANKING_PRECOMPUTED_CONTAINER_NAMES": ["ranker_precom"],
    "RECOMMENDER_CONTAINER_NAMES": ["recommender_base"],
    "RECOMMENDER_PRECOMPUTED_CONTAINER_NAMES": ["recommender_precom"],
}


def _configure(app, **overrides):
    app.config.update({**SYSTEM_CONFIG, **overrides})


def _names():
    return sorted(name for (name,) in db.session.query(System.name).all())


def test_seed_db_adds_all_systems(app):
    _configure(app)
    with app.app_context():
        seed_db()

        assert _names() == sorted(
            [
                "ranker_base",
                "ranker",
                "ranker_precom",
                "recommender_base",
                "recommender_precom",
            ]
        )
        precom = db.session.query(System).filter_by(name="ranker_precom").one()
        assert (precom.type, precom.system_type) == ("RANK", "PRECOM")
        rec = db.session.query(System).filter_by(name="recommender_base").one()
        assert (rec.type, rec.system_type) == ("REC", "LIVE")


def test_seed_db_twice_does_not_duplicate(app):
    _configure(app)
    with app.app_context():
        seed_db()
        added = seed_db()

        assert added == []
        assert len(_names()) == len(set(_names())) == 5


def test_seed_db_skips_existing_system_and_keeps_its_config(app):
    _configure(app)
    with app.app_context():
        db.session.add(
            System(
                name="ranker",
                type="RANK",
                system_type="PRECOM",
                num_requests=42,
                num_requests_no_head=7,
            )
        )
        db.session.commit()

        seed_db()

        rankers = db.session.query(System).filter_by(name="ranker").all()
        assert len(rankers) == 1
        assert rankers[0].system_type == "PRECOM"
        assert rankers[0].num_requests == 42


def test_seed_db_ignores_duplicate_names_in_config(app):
    _configure(app, RANKING_PRECOMPUTED_CONTAINER_NAMES=["ranker"])
    with app.app_context():
        seed_db()

        rankers = db.session.query(System).filter_by(name="ranker").all()
        assert len(rankers) == 1
        assert rankers[0].system_type == "LIVE"
