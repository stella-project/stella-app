from datetime import datetime
from uuid import uuid4
from app.models import db, Session, System

from pytz import timezone

tz = timezone("Europe/Berlin")


def create_new_session(container_name=None, sid=None, type=None):
    """
    create a new session and set experimental ranking and recommender-container for session

    @param container_name:      ranking container name (str)
    @param container_rec_name:  recommendation container name (str)

    @return:                    session-id (int)
    """

    if sid is None or not isinstance(sid, str):
        sid = uuid4().hex

    if container_name:
        container_id = (
            db.session.query(System).filter_by(name=container_name).first().id
        )
    else:
        container_id = None

    if type == "ranker":
        system_ranking = container_id
        system_recommendation = None
    elif type == "recommendation":
        system_ranking = None
        system_recommendation = container_id
    else:
        raise ValueError(
            "Invalid type. Must be 'ranker' or 'recommendation'."
        )

    session = Session(
        id=sid,
        start=datetime.now(tz).replace(tzinfo=None),
        system_ranking=system_ranking,
        system_recommendation=system_recommendation,
        site_user="unknown",
        exit=False,
        sent=False,
    )
    db.session.add(session)

    db.session.commit()

    return session.id
