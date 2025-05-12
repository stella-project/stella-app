from app.models import Session, Result
from app.services.session_service import create_new_session


def test_create_new_session_ranker(client, systems, db_session):
    session_id = create_new_session(
        container_name="ranker_base", sid=None, type="ranker"
    )

    session = db_session.query(Session).first()
    assert session_id == session.id
    assert session.system_ranking == 1


def test_create_new_session_recommender(client, systems, db_session):
    session_id = create_new_session(
        container_name="recommender_base", sid=None, type="recommendation"
    )

    session = db_session.query(Session).filter_by(id=session_id).first()

    assert session_id == session.id
    assert session.system_recommendation == 3
