from application import db
import json
from sqlalchemy.ext import mutable
from sqlalchemy_utils import ScalarListType

class User(db.Model):

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.Text)
    username = db.Column(db.Text, unique = True)
    password = db.Column(db.Text)

    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password

class Friend(db.Model):

    __tablename__ = "friends"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.Text, nullable = False)
    interests = db.Column(db.Text, default="")
    dislikes = db.Column(db.Text, default="")
    quotes = db.Column(db.Text, default="")
    todos = db.Column(db.Text, default="")
    plans = db.Column(db.Text, default="")
    stories = db.Column(db.Text, default="")
    events = db.Column(db.Text, default="")
    work = db.Column(db.Text, default="")
    general = db.Column(db.Text, default="")

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

#Hastags' IDs
class Hashtag(db.Model):

    __tablename__ = "hashtags"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    hashtag = db.Column(db.Text, unique = True)
    bullet_ids = db.Column(ScalarListType(int))

    def __init__(self, hashtag):
        self.hashtag = hashtag
        self.bullet_ids = []

#Bullet points
class Bullet(db.Model):

    __tablename__ = "bullets"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    hashtag_id = db.Column(db.Integer, db.ForeignKey("hashtags.id"), nullable = False)
    friend_id = db.Column(db.Integer, db.ForeignKey("friends.id"), nullable = False)
    category = db.Column(db.Text, default="", nullable = False)
    content = db.Column(db.Text, default="", nullable = False)

    def __init__(self, hashtag_id, friend_id, category, content):
        self.hashtag_id = hashtag_id
        self.friend_id = friend_id
        self.category = category
        self.content = content

db.create_all()