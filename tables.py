from application import db
import json
from sqlalchemy.ext import mutable

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
    name = db.Column(db.Text)
    interests = db.Column(db.Text)
    dislikes = db.Column(db.Text)
    quotes = db.Column(db.Text)
    todos = db.Column(db.Text)
    plans = db.Column(db.Text)
    stories = db.Column(db.Text)
    work = db.Column(db.Text)
    general = db.Column(db.Text)

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

class Note(db.Model):

    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    friend_id = db.Column(db.Integer, db.ForeignKey('friends.id'))
    type = db.Column(db.Text, nullable = False)
    content = db.Column(db.Text, nullable = False)

    def __init__(self, friend_id, type, content):
        self.friend_id = friend_id
        self.type = type
        self.content = content

class JsonEncodedDict(db.TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    #SQL Json storage code by Michael Cho: https://www.michaelcho.me/article/json-field-type-in-sqlalchemy-flask-python
    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)

mutable.MutableDict.associate_with(JsonEncodedDict)

class Hashtag(db.Model):

    __tablename__ = "hashtags"
    hashtag = db.Column(db.Text, primary_key = True)
    notes = db.Column(JsonEncodedDict, nullable = False) #json storage of all notes with this hashtag

    def __init__(self, hashtag, notes):
        self.hashtag = hashtag
        self.notes = notes

db.create_all()