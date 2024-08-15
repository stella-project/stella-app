from flask import request
from . import api
from app.models import db, Session


@api.route("/sessions/<int:sid>/exit", methods=["PUT"])
def exit_session(sid):

    # 1) check if session exists
    # 2) check if session is already exited

    session = Session.query.get_or_404(sid)

    if not session.exit:
        session.exit = True

    db.session.add(session)
    db.session.commit()

    return "", 204


@api.route("/sessions/<int:sid>/user", methods=["POST"])
def post_user(sid):
    session = Session.query.get_or_404(sid)
    session.site_user = request.values.get("site_user", None)
    db.session.add(session)
    db.session.commit()

    return "".join(["POST user", str(session.site_user), "to session", str(sid)]), 201
