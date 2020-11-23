from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.String(64), primary_key=True)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    site_user = db.Column(db.String(64), index=True)
    system_ranking = db.Column(db.Integer, db.ForeignKey('systems.id'))
    system_recommendation = db.Column(db.Integer, db.ForeignKey('systems.id'))
    feedbacks = db.relationship('Feedback', backref='session', lazy='dynamic')
    exit = db.Column(db.Boolean)
    sent = db.Column(db.Boolean)


class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    system_id = db.Column(db.Integer, db.ForeignKey('systems.id'))
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedbacks.id'))
    type = db.Column(db.String(64), index=True)
    q = db.Column(db.String(64), index=True)
    q_date = db.Column(db.DateTime, nullable=True)
    q_time = db.Column(db.Integer)  # which datatype?
    num_found = db.Column(db.Integer)
    page = db.Column(db.Integer)
    rpp = db.Column(db.Integer)
    items = db.Column(db.JSON)
    tdi = db.Column(db.Integer, db.ForeignKey('results.id'))

    @property
    def serialize(self):
        return {'rid': self.id,
                'session_id': self.session_id,
                'system_id': self.system_id,
                'feedback_id': self.feedback_id,
                'type': self.type,
                'q': self.q,
                'q_date': self.q_date,
                'q_time': self.q_time,
                'num_found': self.num_found,
                'page': self.page,
                'rpp': self.rpp,
                'items': self.items,
                'tdi': self.tdi}


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'))
    interleave = db.Column(db.Boolean)
    results = db.relationship('Result', backref='feedback', lazy='dynamic')
    clicks = db.Column(db.JSON)


class System(db.Model):
    __tablename__ = 'systems'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    type = db.Column(db.String(64), index=True)
    results = db.relationship('Result', backref='system', lazy='dynamic')
    num_requests = db.Column(db.Integer)