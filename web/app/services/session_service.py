from datetime import datetime, timezone
from uuid import uuid4

from app.models import Session, System, db


def create_new_session(container_name=None, sid=None, system_type=None):
    """Create a new session and assign the experimental system to it.

    Args:
        container_name (str, optional): Name of the experimental system container.
        sid (str, optional): Session ID to use. A random one is generated if missing.
        system_type (str): Type of the system, either "ranking" or "recommendation".

    Returns:
        str: The session ID.
    """

    if sid is None or not isinstance(sid, str):
        sid = uuid4().hex

    if container_name:
        container_id = (
            db.session.query(System).filter_by(name=container_name).first().id
        )
    else:
        container_id = None

    if system_type == "ranking":
        system_ranking = container_id
        system_recommendation = None
    elif system_type == "recommendation":
        system_ranking = None
        system_recommendation = container_id
    else:
        raise ValueError(
            f"Invalid system type {system_type!r}. Must be 'ranking' or 'recommendation'."
        )

    session = Session(
        id=sid,
        start=datetime.now(timezone.utc).replace(tzinfo=None),
        system_ranking=system_ranking,
        system_recommendation=system_recommendation,
        site_user="unknown",
        exit=False,
        sent=False,
    )
    db.session.add(session)

    db.session.commit()

    return session.id
