from flask import request
from . import api
from app.models import db, Session


@api.route("/sessions/<string:sid>/exit", methods=["PUT"])
def exit_session(sid):
    """
    Exits a session by its ID.
    ---
    tags:
      - Session
    description: |
      Sets the `exit` flag of the specified session to `True`.  
      Used when a user closes or explicitly terminates a session.
    parameters:
      - name: sid
        in: path
        type: string
        required: true
        description: Unique session ID to mark as exited.
    responses:
      204:
        description: Session successfully marked as exited.
      404:
        description: Session not found.
    """
    session = db.session.query(Session).get_or_404(sid)

    if not session.exit:
        session.exit = True
        db.session.add(session)
        db.session.commit()
        return "", 204


@api.route("/sessions/<string:sid>/user", methods=["POST"])
def post_user(sid):
    """
    Adds a user ID to a session by the session ID.
    ---
    tags:
      - Session
    description: |
      Associates a `site_user` with an existing session.  
      This can be used to link authenticated users to active sessions.
    parameters:
      - name: sid
        in: path
        type: string
        required: true
        description: Unique session ID.
      - name: site_user
        in: formData
        type: string
        required: true
        description: User identifier to attach to the session.
    responses:
      201:
        description: User successfully added to the session.
        schema:
          type: object
          properties:
            message:
              type: string
              example: "POST user user123 to session sess456"
      400:
        description: Missing or invalid `site_user` value.
      404:
        description: Session not found.
    """
    session = db.session.query(Session).get_or_404(sid)
    session.site_user = request.values.get("site_user", None)
    db.session.add(session)
    db.session.commit()
    return f"POST user {session.site_user} to session {sid}", 201
