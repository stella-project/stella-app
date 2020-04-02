from . import api
from core.models import db, Session


@api.route('/sessions/<int:sid>/exit', methods=['PUT'])
def exit_session(sid):

    # 1) check if session exists
    # 2) check if session is already exited

    session = Session.query.get_or_404(sid)

    if not session.exit:
        session.exit = True

    db.session.add(session)
    db.session.commit()

    return '', 204
