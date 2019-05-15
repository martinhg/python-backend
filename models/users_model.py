from sqlalchemy import Integer, String, DateTime
from database import db
from datetime import datetime

notifications_per_users = db.Table('notifications_per_users',
                                   db.Column('notifications_id', db.Integer, db.ForeignKey('notifications.id')),
                                   db.Column('users_id', db.Integer, db.ForeignKey('users.id')))


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(), unique=True, nullable=False)
    password = db.Column(String(), nullable=False)
    fcm_token = db.Column(String(), nullable=True)
    notifications = db.relationship("Notification", secondary=notifications_per_users, uselist=True)

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(), nullable=False)
    message = db.Column(String(), nullable=False)
    datetime = db.Column(DateTime, nullable=False)
    users = db.relationship("User", secondary=notifications_per_users,
                            cascade="save-update, merge", uselist=True)

    def __init__(self, title, message):
        self.title = title
        self.message = message
        self.datetime = datetime.now()


class Messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(Integer(), primary_key=True)
    message = db.Column(String(), nullable=False)
    created_at = db.Column(DateTime(), nullable=False, default=datetime.now())
    user_sender_id = db.Column(Integer(), db.ForeignKey('users.id'), nullable=False)
    user_receiver_id = db.Column(Integer(), db.ForeignKey('users.id'), nullable=False)

    def __init__(self, message=None, user_sender_id=None, user_receiver_id=None):
        self.message = message
        self.user_sender_id = user_sender_id
        self.user_receiver_id = user_receiver_id
