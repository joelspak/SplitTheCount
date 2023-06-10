import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///count.db")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show counts"""
    if request.method == "GET":
        i = 0
        a = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        username = a[0]["username"]
        cuentas = db.execute("SELECT * FROM cuentas WHERE usuario = :user", user=username)

    return render_template("index2.html",  cuentas=cuentas)


@app.route("/count", methods=["GET", "POST"])
@login_required
def count():
    """add Counts"""
    if request.method == "GET":
        return render_template("count.html")
    else:
        cantidad = int(request.form.get("cantidad"))
        return render_template("count2.html", cantidad=cantidad)


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """see history of pays of a bill"""
    if request.method == "GET":
        a = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        username = a[0]["username"]
        b = db.execute("SELECT * FROM cuentas WHERE usuario = :username", username=username)
        return render_template("history.html", b=b)
    else:
        cuenta = request.form.get("cuenta")
        a = db.execute("SELECT * FROM cuentas WHERE cuenta = :cuenta", cuenta=cuenta)
        b = db.execute("SELECT * FROM pagos WHERE cuenta = :cuenta", cuenta=cuenta)
        usuarios = len(a)
        return render_template("history2.html", a=a, b=b, usuarios=usuarios)



@app.route("/count2", methods=["GET", "POST"])
@login_required
def new_count():
    """add Counts"""
    usuarios = {}
    i = 0
    if request.method == "POST":
        input_names = [name for name in request.form.keys() if name.startswith('user_')]
        for input_name in input_names:
            usuarios[i] = request.form[input_name]
            i = i + 1
        cuenta = request.form.get("cuenta")
        saldo = 0
        valores = usuarios.values()
        for user in valores:
          #  a = db.execute("SELECT * FROM users WHERE username = :user", user=user)
            b = db.execute("INSERT INTO cuentas (usuario, cuenta, saldo) VALUES (:us, :cuenta, :saldo)", us=user, cuenta=cuenta, saldo=saldo)

        return render_template("count3.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/pay", methods=["GET", "POST"])
@login_required
def pay():
    """new pay"""
    if request.method == "GET":
        c = {}
        users = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        username = users[0]["username"]
        a = db.execute("SELECT * FROM cuentas WHERE usuario = :username", username=username)
        for row in a:
            b = db.execute("SELECT * FROM cuentas WHERE cuenta = :cuenta", cuenta=row["cuenta"])
            c[row["cuenta"]] = []
            i = 0
            while i < len(b):
                c[row["cuenta"]].append(b[i]["usuario"])
                i = i + 1
        return render_template("pay.html", systems=c)
    else:
        users = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        username = users[0]["username"]
        a = db.execute("SELECT * FROM cuentas WHERE usuario = :username", username=username)
        count = request.form.get("bill")
        money = int(request.form.get("money"))
        who_paid = request.form.get("who_paid")
        applies_to = request.form.getlist("applies_to")
        motivo = request.form.get("motivo")

        fecha = datetime.now()
        cantidad_deudores = 0

        for deudor in applies_to:
            cantidad_deudores = cantidad_deudores + 1

        division = money / cantidad_deudores
# inserto dinero de quein pagó
        db.execute("INSERT INTO pagos (usuario, cuenta, plata, signo_plata, fecha, motivo) VALUES (:usuario, :cuenta, :plata, :signo_plata, :fecha, :motivo)", usuario=who_paid, cuenta=count, plata=money, signo_plata=1, fecha=fecha, motivo=motivo)
        a = db.execute("SELECT * FROM cuentas WHERE usuario = :username AND cuenta = :cuenta", username=who_paid, cuenta=count)
        saldo = a[0]["saldo"] + money
        db.execute("UPDATE cuentas SET saldo = :saldo WHERE usuario = :usuario AND cuenta = :cuenta", saldo=saldo, usuario=who_paid, cuenta=count)
# inserto dinero de los deudores, puede estar incluido el que pagó o no.
        for deudor in applies_to:
            signo_plata = -1
            db.execute("INSERT INTO pagos (usuario, cuenta, plata, signo_plata, fecha, motivo) VALUES (:usuario, :cuenta, :plata, :signo_plata, :fecha, :motivo)", usuario=deudor, cuenta=count, plata=division, signo_plata=signo_plata, fecha=fecha, motivo=motivo)
            a = db.execute("SELECT * FROM cuentas WHERE usuario = :username AND cuenta = :cuenta", username=deudor, cuenta=count)
            saldo = a[0]["saldo"]
            saldo = saldo - division
            db.execute("UPDATE cuentas SET saldo = :saldo WHERE usuario = :usuario AND cuenta = :cuenta", saldo=saldo, usuario=deudor, cuenta=count)

        return render_template("pay_post.html", division=division, cantidad_deudores=cantidad_deudores, user=username, count=count, money=money, applies_to=applies_to, who_paid=who_paid, motivo=motivo)




@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
     # Ensure username was submitted
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        pw = request.form.get("password")
        confirmation = request.form.get("confirmation")
        num = 0
        may = 0
        min = 0
        passok = 0
        for c in pw:
            if c.isupper():
                may = may + 1
            elif c.islower():
                min = min + 1
            elif c.isdigit():
                num = num + 1
            if may >= 1 and min >= 1 and num >= 1:
                passok = 1

        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not pw:
            return apology("must provide password", 403)

        # Ensure confirmation password is equal to password
        elif not pw == confirmation:
            return apology("password does not match", 403)

        # Ensure password has at least eight characters.
        elif not len(pw) >= 8 or passok == 0:
            return apology("low security password. Try again ", 403)

        # Check if exists username in database
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        if len(rows) == 1:
            return apology("username already exists", 403)


        password=generate_password_hash(pw)
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=password)

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
