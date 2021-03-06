from flask import Flask, flash, redirect, render_template, request, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from flask_session import Session
from flask_jsglue import JSGlue
from sqlalchemy.orm import load_only

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
    #Delete friends and associated bullets
    friends = Friend.query.filter_by(user_id = session["user_id"]).all()
    if friends != None:
        for friend in friends:
            #Delete bullets in friends
            bullets = Bullet.query.filter_by(friend_id = friend.id).all()
            if bullets != None:
                for bullet in bullets:
                    #Delete hashtag records of the bullet
                    b_ids = Hashtag.query.get(bullet.hashtag_id).bullet_ids
                    if bullet.id in b_ids:
                        b_ids.remove(bullet.id)
                        #Delete empty hashtags
                        if b_ids == []:
                            Hashtag.query.filter_by(id=bullet.hashtag_id).delete()
                        else:
                            Hashtag.query.get(bullet.hashtag_id).bullet_ids = b_ids
                            db.session.commit()
                    Bullet.query.filter_by(id=bullet.id).delete()
                Friend.query.filter_by(id=friend.id).delete()
    #delete user
    User.query.filter_by(id=session["user_id"]).delete()
    db.session.commit()
    session.clear()
    return render_template("login.html", message="Account successfully deleted!")

@app.route("/")
@login_required
def index():
    """Index"""
    #get user's name
    user = User.query.filter(User.id==session["user_id"]).first()
    #count friends
    count = Friend.query.filter(Friend.user_id == session["user_id"]).count()
    return render_template("index.html", name=user.name, count=count)

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
            return apology("Please enter a name or interest into the search bar above.")
        #Search by name(not case sensitive)
        friend = Friend.query.filter(Friend.name.contains(item), Friend.user_id == session["user_id"]).first()
        if not friend:
            #check if it's a hashtag
            if item[0] != '#':
                item = '#' + item
            hashtag = Hashtag.query.filter(Hashtag.hashtag==item.lower()).first()
            if not hashtag:
                return apology("No results! Please check your spelling and entire only one item!")
            return redirect(url_for('tag', h_id=hashtag.id))
        return displayFriend(friend)

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

        #create friend while checking for duplicates
        temp_name = name
        name_count = 1
        while True:
            if Friend.query.filter_by(name=temp_name, user_id=session["user_id"]).count() > 0:
                name_count += 1
                temp_name = name + " " +str(name_count)
            else:
                break

        friend = Friend(session["user_id"], temp_name)
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
        message = "{} Added!".format(temp_name)
        if name_count > 1:
            message += "Note: There are " + str(name_count) + " {}s on your friend list".format(name)

        return displayFriend(friend, message)

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

    #clear bullet points stored for this friend
    if Bullet.query.all() != None and Bullet.query.filter(Bullet.friend_id==id).count() > 0:
        bps = Bullet.query.filter(Bullet.friend_id==id).all()
        for bp in bps:
            b_ids = Hashtag.query.filter(Hashtag.id==bp.hashtag_id).first().bullet_ids
            if bp.id in b_ids:
                b_ids.remove(bp.id)
                Hashtag.query.filter(Hashtag.id==bp.hashtag_id).first().bullet_ids = b_ids
                db.session.commit()

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
    if request.form["name"] != "":
        friend.name = request.form["name"]
    db.session.commit()
    session.pop("friend_id", None)

    return displayFriend(friend, "Updated!")

@app.route("/tags", methods=["GET"])
@login_required
def tags():
    """Display hashtags alphabetically"""
    hashtags = Hashtag.query.order_by(Hashtag.hashtag.asc())
    taglist = []
    for hashtag in hashtags:
        if session["user_id"] in hashtag.user_ids:
            taglist.append(hashtag)
    return render_template("tags.html", hashtags = taglist)

@app.route("/tag", methods=["GET"])
@login_required
def tag():
    """Display bullet points associated to a specific hashtag"""
    id = request.args.get("h_id")
    bullets = Bullet.query.filter(Bullet.hashtag_id == id)

    #gather friends that are tagged in each category
    interests = categorize(bullets, 'interest')
    dislikes = categorize(bullets, 'dislike')
    quotes = categorize(bullets, 'quote')
    todos= categorize(bullets, 'todo')
    plans = categorize(bullets, 'plan')
    stories = categorize(bullets, 'story')
    events = categorize(bullets, 'event')
    work = categorize(bullets, 'work')
    general = categorize(bullets, 'note')

    return render_template("tag.html", bullets=bullets, interests=interests, dislikes=dislikes, quotes=quotes, todos=todos, plans=plans, stories=stories, events=events, work=work, general=general)

if __name__ == '__main__':
    app.run(debug=True)