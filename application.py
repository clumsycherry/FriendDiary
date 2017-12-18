from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask_session import Session

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#SQL Alchemy
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///people.db"
app.config["SQLALCHEMY_ECHO"] = True

# configure to use SQLAlchemy database
db = SQLAlchemy(app)

from tables import *
from helpers import *

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        username = request.form.get("username")
        if not username:
            return apology("must provide username")

        # ensure password was submitted
        password = request.form.get("password")
        if not password:
            return apology("must provide password")

        # ensure username exists and password is correct
        user = User.query.filter(User.username==username).first()
        if not user:
            return apology("Invalid username and password combination")
        if not pwd_context.verify(password, user.password):
            return apology("Invalid username and password combination")

        # remember which user has logged in
        session["user_id"] = user.id

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]
        password2 = request.form["password2"]

        #username and passwords must be filled in, passwords must match
        if name == "":
            return apology("Missing Name")
        if username == "":
            return apology("Missing username")
        if password == "" or password2 == "":
            return apology("Please enter your password twice")
        if password != password2:
            return apology("Passwords must match")

        #check if username taken
        if User.query.filter(User.username == username).count() > 0:
           return apology(username + " is taken", "Please select new username")

        #add user
        user = User(name, username, pwd_context.hash(password))
        db.session.add(user)
        db.session.commit()

        return render_template("login.html", message="Registration successful! Please log in:")
    else:
        return render_template("login.html")

@app.route("/unregister")
@login_required
def unregister():
    """Unregister user."""
    User.query.filter(User.id == session["user_id"]).delete()
    db.session.commit()
    return render_template("login.html", message="Successfully unregistered!")

@app.route("/")
@login_required
def index():
    """Index"""
    #get user's name
    user = User.query.filter(User.id==session["user_id"]).first()
    return render_template("index.html", name=user.name)

@app.route("/search", methods=["GET","POST"])
@login_required
def search():
    """Search for Friend or Interest"""
    if request.method == "GET":
        return render_template("search.html", item="Enter search item above")

    if request.method == "POST":
        item = request.form["item"]
        if item == "":
            return apology("Invalid Search")

        #Search by name(not case sensitive)
        friends = Friend.query.filter(Friend.name.contains(item), Friend.user_id == session["user_id"]).all()
        if not friends:
            return apology("No results!")
        result = ""
        for friend in friends:
            result += friend.name + " "

        #gather interests
        friend1 = friends[0]
        notes = Note.query.filter(Note.friend_id==friend1.id).all()
        interests = []
        for note in notes:
            if note.type == "Interest":
                interests.append(note.content)

        return render_template("search.html", item=result, interests=interests)

@app.route("/addfriend", methods=["GET", "POST"])
@login_required
def addfriend():
    """Adds a new friend to database"""
    if request.method == "GET":
        return render_template("addfriend.html")

    if request.method == "POST":
        #check for name input
        name = request.form["name"]
        if name == "":
            return render_template("addfriend.html", message = "Must fill in a friend's name")

        #add friend
        friend = Friend(session["user_id"], name)
        db.session.add(friend)
        db.session.commit()

        #add interest if listed
        interest = request.form["interest"]
        if interest != "":
            session["friend_id"] = friend.id
            addInterest(interest)
            session.pop("friend_id", None)

        return render_template("addfriend.html", message = "Friend added!")