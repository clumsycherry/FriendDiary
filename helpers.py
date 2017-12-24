import csv
import re
import sys
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

def check(value, category=""):
    """Returns a textarea value if not blank"""
    #having only bullet points is considered blank
    if value.strip().strip("•") == "":
        return ""

    #Special characters: http://www.regular-expressions.info/dotnet.html
    #break into bullet points
    bullets = value.split("•")
    for bullet in bullets:
        words = bullet.split()
        for word in words:
            #check for hashtags
            if word[0] == "#" and word != "#":
                word = word.lower()

                #check for special characters and contains letters
                if re.match("^[a-z0-9]*$", word[1:]):
                    hashtag = Hashtag.query.filter(Hashtag.hashtag == word).first()

                    #create hashtag if hashtag doesn't exist yet
                    if hashtag is None:
                        db.session.add(Hashtag(word))
                        hashtag = Hashtag.query.order_by(Hashtag.id.desc()).first()

                    #check to see if the same hashtag exists in the same bullet point

                    if Bullet.query.filter(Bullet.friend_id==session["friend_id"], Bullet.hashtag_id == hashtag.id).count() < 1:
                        #if unique, add current bullet point to hashtag
                        b = Bullet(hashtag.id, session["friend_id"], category, bullet)
                        db.session.add(b)
                        b = Bullet.query.order_by(Bullet.id.desc()).first()
                        hashtag.bullet_ids = hashtag.bullet_ids + [b.id]

    db.session.commit()
    return value
