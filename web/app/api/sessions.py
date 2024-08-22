from flask import request
from . import api
from app.models import db, Session


@api.route("/sessions/<string:sid>/exit", methods=["PUT"])
def exit_session(sid):
    """Exit a session by its ID.
    Tested: True
    """
    session = db.session.query(Session).get_or_404(sid)

    if not session.exit:
        session.exit = True
        db.session.add(session)
        db.session.commit()
        return "", 204


@api.route("/sessions/<string:sid>/user", methods=["POST"])
def post_user(sid):
    """Add a user ID to a session by the session ID.
    Tested: True
    """
    session = db.session.query(Session).get_or_404(sid)
    session.site_user = request.values.get("site_user", None)
    db.session.add(session)
    db.session.commit()
    return f"POST user {session.site_user} to session {sid}", 201
