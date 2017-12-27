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
    if value.strip().strip("•")=="":
        return ""
    #having multiple bullet points is also considered blank
    if "".join(value.split("•")).strip() == "":
        return ""

    #Special characters: http://www.regular-expressions.info/dotnet.html
    #break into bullet points
    bullets = value.split("•")
    for bullet in bullets:
        current_hashtag = "" #for checking if hashtag is still the same
        words = bullet.split()
        for word in words:
            #check for hashtags
            if word[0] == "#" and word != "#":
                word = word.lower()

                #check for special characters and contains letters
                if re.match("^[a-z0-9]*$", word[1:]):

                    #create hashtag if hashtag doesn't exist yet
                    hashtag = Hashtag.query.filter(Hashtag.hashtag == word).first()
                    if hashtag is None:
                        db.session.add(Hashtag(word))
                        hashtag = Hashtag.query.order_by(Hashtag.id.desc()).first()

                    #add bullet entry if the hashtag doesn't already exist in the current bullet point
                    if word != current_hashtag:
                        b = Bullet(hashtag.id, session["friend_id"], category, bullet)
                        db.session.add(b)
                        b = Bullet.query.order_by(Bullet.id.desc()).first()

                        #keep track of bullet and user ids for each hashtag
                        hashtag.bullet_ids = hashtag.bullet_ids + [b.id]

                        #add user id to hashtag table
                        if session["user_id"] not in hashtag.user_ids:
                            hashtag.user_ids = hashtag.user_ids + [session["user_id"]]
                    db.session.commit()
                    current_hashtag = word

    db.session.commit()
    return value

def categorize(bullets, cat=""):
    """Returns list of dict objects after filtering through bullet points for a specific category."""
    bulletlist = []
    q = bullets.filter_by(category=cat).all()
    for bullet in q:
        d = {
            "name": Friend.query.get(bullet.friend_id).name,
            "id": bullet.friend_id,
            "content": bullet.content
        }
        bulletlist.append(d)
    return bulletlist