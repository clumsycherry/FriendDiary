from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

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

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///people.db")

@app.route("/")
@login_required
def index():
    #get user's name
    id = session["user_id"]
    name = db.execute("SELECT name FROM users WHERE id = :id", id=id)[0]["name"]
    return render_template("index.html", name=name)

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    id = session["user_id"]

    #make a hashtable for stocks to display
    stocks = []
    records = db.execute("SELECT * FROM records WHERE id = :id", id=id)
    for record in records:
        symbol = record["stock"]
        stocks.append({"symbol": symbol, "name": lookup(symbol)["name"], "share": record["share"], "price": usd(record["price"]), "timestamp": record["timestamp"]})

    return render_template("history.html", stocks=stocks)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

        #encrypt password and add unique users to database
        hash = pwd_context.hash(password)
        unique = db.execute("INSERT INTO users (username, hash, name) VALUES (:username, :hash, :name)", username = username, hash = hash, name=name)
        if not unique:
            return apology(username + " is taken", "please select new username")

    return render_template("login.html", message="Registration successful! Please log in:")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "GET":
        return render_template("buy.html")
    elif request.method == "POST":

        #stock symbol cannot be blank
        symbol = request.form["symbol"]
        if symbol == "":
            return apology("Missing", "Stock Symbol")

        #check if number of shares is valid
        share = request.form["share"]
        if share == "":
            return apology("Missing", "Number of Shares")

        share = int(share)
        if share < 1:
            return apology("Number of shares must be more than 0")

        #calculate cost
        stock = lookup(symbol)
        if stock == None:
            return apology("Invalid Symbol", symbol)
        symbol = stock["symbol"]
        price = stock["price"]
        cost = price * share

        #see if user has enough money to purchase
        id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=id)[0]["cash"]
        if cash < cost:
            return apology("Cost exceeds your current balance", "Cannot purchase stocks")

        #update user cash
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=cash-cost, id=id)

        #update purchase records
        db.execute("INSERT INTO records (id, stock, share, price) VALUES (:id, :stock, :share, :price)", id=id, stock=symbol, share=share, price=price)

        flash("Success! You just bought {} share(s) of {} at {} per share.".format(share, stock["name"], usd(price)), 'info')
        return redirect(url_for("index"))

    #homepage will show purchase results
    return redirect(url_for("index"))

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "GET":
        return render_template("sell.html")
    elif request.method == "POST":
        #stock symbol cannot be blank
        symbol = request.form["symbol"]
        if symbol == "":
            return apology("Missing", "Stock Symbol")

        #check if number of shares is valid
        share = request.form["share"]
        if share == "":
            return apology("Missing", "Number of Shares")
        share = int(share)
        if share < 1:
            return apology("Number of shares must be more than 0")

        #see if user has enough shares to sell
        stock = lookup(symbol)
        if stock == None:
            return apology("Invalid Symbol", symbol)

        #check if enough shares to sell
        id = session["user_id"]
        symbol = stock["symbol"]
        usershares = db.execute("SELECT SUM(share) FROM records WHERE id =:id AND stock= :stock", id=id, stock=symbol)
        if not usershares or share > usershares[0]["SUM(share)"]:
            return apology("You do not own enough shares to sell", "Transaction Failed")

        #update sale record
        price = stock["price"]
        db.execute("INSERT INTO records (id, stock, share, price) VALUES (:id, :stock, :share, :price)", id=id, stock=symbol, share=share*-1, price=price)

        #update user cash
        cash = db.execute("SELECT cash FROM users WHERE id = :id", id=id)[0]["cash"] + (price * share)
        db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=cash, id=id)

        flash("Success! You just sold {} share(s) of {} at {} per share.".format(share, stock["name"], usd(price)), 'info')
        return redirect(url_for("index"))

    #homepage will show purchase results
    return redirect(url_for("index"))

@app.route("/minusone")
@login_required
def minusone():
    """Sell 1 share of a certain stock from the index page."""
    #obtain stock symbol from index button
    symbol = request.args.get('symbol', None)
    stock = lookup(symbol)

    #see if user has enough shares to sell
    id = session["user_id"]
    usershares = db.execute("SELECT SUM(share) FROM records WHERE id =:id AND stock= :stock", id=id, stock=symbol)
    if usershares[0]["SUM(share)"] < 1:
        return apology("You do not own enough shares to sell", "Transaction Failed")

    #update sale record
    price = stock["price"]
    db.execute("INSERT INTO records (id, stock, share, price) VALUES (:id, :stock, :share, :price)", id=id, stock=symbol, share= -1, price=price)

    #update user cash
    cash = price + db.execute("SELECT cash FROM users WHERE id = :id", id=id)[0]["cash"]
    db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash=cash, id=id)

    flash("Success! You just sold a share of {} for {}.".format(stock["name"], usd(price)), 'info')
    return redirect(url_for("index"))

@app.route("/plusone")
@login_required
def plusone():
    """Buy 1 share of a certain stock from the index page."""
    #obtain stock symbol from index button
    symbol = request.args.get('symbol', None)
    stock = lookup(symbol)

    #see if user has enough cash to buy stock
    id = session["user_id"]
    price = stock["price"]
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=id)[0]["cash"]
    if cash < price:
        return apology("Cost exceeds your current balance", "Cannot purchase this stock")

    #update sale record
    db.execute("INSERT INTO records (id, stock, share, price) VALUES (:id, :stock, :share, :price)", id=id, stock=symbol, share= 1, price=price)

    #update user cash
    db.execute("UPDATE users SET cash = :cash WHERE id = :id", cash= cash-price, id=id)

    flash("Success! You just bought a share of {} for {}.".format(stock["name"], usd(price)), 'info')
    return redirect(url_for("index"))

@app.route("/search", methods=["POST"])
@login_required
def search():
    """Search for Friend or Interest"""
    item = request.form["item"]
    if item == "":
        return apology("Invalid Search")
    return render_template("search.html", item=item)