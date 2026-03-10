from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    visited_duraks = db.relationship('UserVisitedDurak', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    durak_notes = db.relationship('UserDurakNote', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    quiz_results = db.relationship('UserQuizResult', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    hap_answers = db.relationship('UserHapAnswer', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reflections = db.relationship('UserReflection', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.is_active_user


class UserVisitedDurak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    durak_id = db.Column(db.Integer, nullable=False)
    visited_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('user_id', 'durak_id'),)


class UserDurakNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    durak_id = db.Column(db.Integer, nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('user_id', 'durak_id'),)


class UserQuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    result_key = db.Column(db.String(50), nullable=False)
    lider_id = db.Column(db.Integer, nullable=False)
    scores_json = db.Column(db.Text, nullable=False)
    taken_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class UserHapAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lider_id = db.Column(db.Integer, nullable=False)
    question_index = db.Column(db.Integer, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('user_id', 'lider_id', 'question_index'),)


class UserReflection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), nullable=False, default='genel')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
