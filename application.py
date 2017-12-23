from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask_session import Session
from flask_jsglue import JSGlue

# configure application
app = Flask(__name__)
JSGlue(app)

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
    """Delete user account."""
    User.query.filter(User.id == session["user_id"]).delete()
    db.session.commit()
    session.clear()
    return render_template("login.html", message="Account successfully deleted!")

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
        #get id from friendlist
        friend_id = request.args.get("id")
        #GET can be called from search bar
        if not friend_id:
            return apology("No results", "Enter name into search bar and check spelling.")
        friend = Friend.query.filter(Friend.id==friend_id).first()
        return displayFriend(friend)

    if request.method == "POST":
        item=request.form["item"]
        if not item:
            return apology("Enter name into search bar and check spelling.")
        #Search by name(not case sensitive)
        friend = Friend.query.filter(Friend.name.contains(item), Friend.user_id == session["user_id"]).first()
        if not friend:
            return apology("No results!")
        return displayFriend(friend)

#@app.route("/search/<item>", methods=["GET"])
#@login_required
#def search_url(item):
#    """Display friend selected on friend's list."""
#    friend = Friend.query.filter(Friend.name == item, Friend.user_id == session["user_id"]).first()
#    if not friend:
#        return apology("No results!")
#    return displayFriend(friend)

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

        #create friend
        friend = Friend(session["user_id"], name)
        db.session.add(friend)

        #grab current/most recent friend from db
        friend = Friend.query.order_by(Friend.id.desc()).first()

        #add notes if listed by category
        session["friend_id"] = friend.id
        friend.interests = check(request.form["interest"], "interest")
        friend.dislikes = check(request.form["dislike"], "dislike")
        friend.quotes = check(request.form["quote"], "quote")
        friend.todos = check(request.form["todo"], "todo")
        friend.plans = check(request.form["plan"], "plan")
        friend.stories = check(request.form["story"], "story")
        friend.events = check(request.form["event"], "event")
        friend.work = check(request.form["work"], "work")
        friend.general = check(request.form["note"], "note")
        db.session.commit()
        session.pop("friend_id", None)

        #check for duplicate entries
        if Friend.query.filter(Friend.name==friend.name).count() > 1:
            message = "{} Added! Note: There are now more than 1 {}s on your friend list".format(name, name)
            return displayFriend(friend, message)

        return displayFriend(friend, "{} Added!".format(name))

@app.route("/friends", methods=["GET"])
@login_required
def friends():
    "Display user's friends in alphabetical order"
    friends = Friend.query.filter(Friend.user_id == session["user_id"]).order_by(func.lower(Friend.name)).all()
    if not friends:
        return apology("Add friends first!")

    return render_template("friends.html", friends = friends)

@app.route("/delete")
@login_required
def delete():
    "Delete a friend"
    Friend.query.filter(Friend.id == request.args.get("id")).delete()
    db.session.commit()
    return redirect(url_for("friends"))

@app.route("/edit", methods=["POST"])
@login_required
def edit():
    """Edit a friend profile"""
    id = request.args.get("id", None)
    friend = Friend.query.filter(Friend.id==id).first()

    #clear friend's data in bullet point table
    Bullet.query.filter(Bullet.friend_id==id).delete()

    #update interests
    session["friend_id"] = id
    friend.interests = check(request.form["interest"], "interest")
    friend.dislikes = check(request.form["dislike"], "dislike")
    friend.quotes = check(request.form["quote"], "quote")
    friend.todos = check(request.form["todo"], "todo")
    friend.plans = check(request.form["plan"], "plan")
    friend.stories = check(request.form["story"], "story")
    friend.events = check(request.form["event"], "event")
    friend.work = check(request.form["work"], "work")
    friend.general = check(request.form["note"], "note")
    db.session.commit()
    session.pop("friend_id", None)

    return displayFriend(friend, "Updated!")