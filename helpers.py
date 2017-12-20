import csv
import urllib.request
from flask import redirect, render_template, request, session, url_for
from functools import wraps
from tables import *

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def apology(message="", detail=""):
    """Renders message as an apology to user."""
    return render_template("apology.html", message=message, detail=detail)

def addInterest(content=""):
    interest = Note(session["friend_id"], "Interest", content)
    db.session.add(interest)
    db.session.commit()

def displayFriend(friend, message=""):
    #gather interests
    notes = Note.query.filter(Note.friend_id==friend.id).all()
    interests = []
    for note in notes:
        if note.type == "Interest":
            interests.append(note.content)
    return render_template("profile.html", item=friend.name, interests=interests, message=message)