import csv
import urllib.request
from flask import render_template, request, session, redirect, url_for
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

def displayFriend(friend, message=""):
    """Return a friend's profile"""
    return render_template("profile.html",
        item=friend.name,
        interest=friend.interests,
        dislike=friend.dislikes,
        quote=friend.quotes,
        todo=friend.todos,
        plan=friend.plans,
        story=friend.stories,
        event=friend.events,
        work=friend.work,
        note=friend.general,
        id=friend.id,
        message=message)

def check(value):
    """Returns a textarea value if not blank"""
    #having only bullet points is considered blank
    if value.strip().strip("•") == "":
        return ""
    return value