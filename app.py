import os
from dotenv import load_dotenv

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp

from helpers import apology, login_required, find_spaces, valid_time, generate_random_password, check_inputs, avg_list, usd, time, heading_number, collapse_number, hash_collapse_number, time_to_float, rate_to_name, START_OF_SERVICE, END_OF_SERVICE, RATES_NAMES, MAX_DURATION_APPOINTMENT
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, timedelta, datetime
from pytz import timezone

load_dotenv("email_conf.env")

# Configure application
app = Flask(__name__)

# Configure mail
# -----
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_DEFAULT_SENDER")
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# app.config['MAIL_SUPPRESS_SEND'] = True

mail = Mail(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filters
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["time"] = time
app.jinja_env.filters["heading_number"] = heading_number
app.jinja_env.filters["collapse_number"] = collapse_number
app.jinja_env.filters["hash_collapse_number"] = hash_collapse_number
app.jinja_env.filters["rate_to_name"] = rate_to_name

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "info.db")

db = SQL(f"sqlite:///{db_path}")

# db = SQL("sqlite:///info.db")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Show main page with the menu and option to change of password, mail, number
@app.route("/")
@login_required
def index():

    # Get info abou the menu
    info = db.execute("SELECT id, name, price, time AS duration, rate FROM menu;")

    # Get diferent formats of present time (in Lisbon)
    now = datetime.now(timezone("Europe/Lisbon"))
    date_now_2 = now.strftime('%Y%m%d%H%M')
    date_now = now.strftime('%Y-%m-%d')
    date_now_2 = float(int(date_now_2[0:8]) + int(date_now_2[8:12]) / 2400.0)

    # Get last update time
    with open('date.txt') as f:
        line = f.readline()

    # If not updated today, update it
    if not line[:10] == date_now:

        # Update rates
        for style in info:

            # Last appointments of witch user who are rated
            rates = db.execute("SELECT MAX(CAST(REPLACE(appointment.date, '-', '') AS decimal) + appointment.hour_minute / 24.0) AS max, rate FROM (appointment, rates) WHERE appointment.rate_id = rates.id AND appointment.style_id = ? AND (CAST(REPLACE(appointment.date, '-', '') AS decimal) + (appointment.hour_minute / 24.0) + ?) <= ? AND appointment.rate_id IS NOT NULL GROUP BY appointment.user_id;", style["id"], style["duration"], date_now_2)

            # If rates exists
            if len(rates) > 0:

                # Calculate average rate
                avg = avg_list(rates, key=lambda value: value["rate"])

                # Update rate
                db.execute("UPDATE menu SET rate = ? WHERE id = ?;", avg, style["id"])
                style["rate"] = avg

        # Update time of last update (now)
        line = now.strftime('%Y-%m-%d %H:%M')
        with open('date.txt', 'w') as f:
            f.write(line)

    # Get next appointment
    next_appoint = db.execute("SELECT MIN(CAST(REPLACE(appointment.date, '-', '') AS decimal) + (appointment.hour_minute) / 24.0) AS min, menu.name, menu.time AS duration, appointment.date, appointment.hour_minute AS time FROM (appointment, menu) WHERE user_id = ? AND appointment.style_id = menu.id AND CAST(REPLACE(appointment.date, '-', '') AS decimal) + (appointment.hour_minute) / 24.0 >= ?;", session["user_id"], date_now_2)
    if not next_appoint[0]["min"]:
        next_appoint = None

    # render portfolio.html with info
    return render_template("portfolio.html", info=info, appointment=next_appoint, last_update=line)


# Ask for input to show available schedule or show the schedule to make an appointment
@app.route("/book_in", methods=["GET", "POST"])
@login_required
def book_in():

    # Get input to show available times to specific style (get input by post)
    if request.method == "POST":

        # Store input
        name = request.form.get("name")
        date_from = request.form.get("date_from")
        date_to = request.form.get("date_to")

        # Check format of input
        result = check_inputs(name, dates=[date_from, date_to])
        if not result == None:
            return apology(result, 400)

        # Check if user gives data after today's date
        date_now = (datetime.now(timezone("Europe/Lisbon")) + timedelta(days=1)).strftime('%Y-%m-%d')
        if date_now > date_from:
            return apology("Bad dates", 400)

        # Check if second date is smaller than fisrt date
        if date_to < date_from:
            return apology("Bad dates", 400)

        # Find info about style_name (and check it exist)
        style_info = db.execute("SELECT id, name, price, time AS duration FROM menu WHERE name = ?;", name)
        if not style_info:
            return apology("Style not founded", 400)
        style_info = style_info[0]

        # Find number of days between input dates
        start_date = date.fromisoformat(date_from)
        end_date = date.fromisoformat(date_to)
        delta = end_date - start_date

        # info with available times
        info = []

        # append available times in info by dates
        for i in range(delta.days + 1):

            # Get appoinments from day being checked
            day = start_date + timedelta(days=i)
            info_day = db.execute("SELECT hour_minute AS time, time AS duration FROM (appointment, menu) WHERE appointment.date = ? AND menu.id = style_id ORDER BY time;", day)

            # Find available sapces in that day
            available = find_spaces(info_day, style_info["duration"])
            if available:
                # if has spaces append it to info
                info.append([available, str(day), i + 1])

        # Send info and info about style and render book_in_available.html
        return render_template("book_in_available.html", info=info, style_info=style_info)

    # If not through post (get)
    else:

        # get info about styles in menu
        info = db.execute("SELECT name, price, time AS duration FROM menu;")

        # Tomorrow date
        date_now = (datetime.now(timezone("Europe/Lisbon")) + timedelta(days=1)).strftime('%Y-%m-%d')

        # Send info and render book_in.html
        return render_template("book_in.html", info=info, date=date_now)


# Store appointment, if available
@app.route("/book_in_validation", methods=["POST"])
@login_required
def book_in_validation():

    if not request.method == "POST":
        return apology("Incorrect methot", 400)

    # Get inout from user
    style_id = request.form.get("style_id")
    day = request.form.get("day")
    time = request.form.get("time")

    # Check format of input
    result = check_inputs(integer=[style_id], time=time, dates=[day])
    if not result == None:
        return apology(result, 400)

    # format of time to float (18:45 = 18,75)
    time = time_to_float(time)

    # Store duration of style (if it exist)
    duration = db.execute("SELECT time, name FROM menu WHERE id = ?;", style_id)
    if not duration:
        return apology("This style doesn't exist")
    duration = duration[0]

    # Find appointment between time of appointment - 2 and time of appointment + duration of appointment
    info_day_2 = db.execute("SELECT hour_minute AS time, time AS duration FROM (appointment, menu) WHERE appointment.date = ? AND hour_minute >= ? AND hour_minute <= ? AND menu.id = style_id;", day, {True: START_OF_SERVICE, False: time - MAX_DURATION_APPOINTMENT}[time - MAX_DURATION_APPOINTMENT < START_OF_SERVICE], {True: END_OF_SERVICE, False: time + duration["time"]}[time + duration["time"] > END_OF_SERVICE])

    # Check if it is a valid time
    if not valid_time(info_day_2, time, duration["time"]):
        return apology("Invalid time", 400)

    # Store the appointment
    db.execute("INSERT INTO appointment (user_id, style_id, date, hour_minute) VALUES(?, ?, ?, ?);", session["user_id"], style_id, day, time)

    info_user = db.execute("SELECT username, email FROM users WHERE id = ?;", session["user_id"])[0]

    message = Message("Appointment registered!", recipients=[info_user["email"]])
    message.html = render_template("in_email.html", name=info_user["username"], style=duration["name"], date=day, time=time)
    mail.send(message)

    # Redirect to main page through
    flash("Appointment registered successfully")
    return redirect("/")


# Mark off an appointment
@app.route("/book_out", methods=["GET", "POST"])
@login_required
def book_out():

    # Mark off an apoointment by request (get input by post)
    if request.method == "POST":

        # Get input
        appoint_id = request.form.get("appoint_id")

        # Check format of input
        result = check_inputs(integer=[appoint_id])
        if not result == None:
            return apology(result, 400)

        # Check if appoointment exist
        info_appoint = db.execute("SELECT user_id, name, username, appointment.date, hour_minute, email FROM (appointment, menu, users) WHERE appointment.style_id = menu.id AND appointment.user_id = users.id AND appointment.id = ?;", appoint_id)
        if not len(info_appoint) == 1:
            return apology("Appointment doesn't exist", 400)

        # Check if it is from current user
        info_appoint = info_appoint[0]
        if not info_appoint["user_id"] == session["user_id"]:
            return apology("Appointment from another user", 400)

        # Delete appointment
        db.execute("DELETE FROM appointment WHERE id = ?;", appoint_id)

        message = Message("Appointment Deleted.", recipients=[info_appoint["email"]])
        message.html = render_template("out_email.html", name=info_appoint["username"], style=info_appoint["name"], date=info_appoint["date"], time=info_appoint["hour_minute"])
        mail.send(message)

        # Redirect to main page
        flash("Marked off successfully")
        return redirect("/")

    # If not through post (get)
    else:

        # Get appointments after and from today
        curr_day = str(date.today())
        info = db.execute("SELECT appointment.id, menu.time AS duration, name, appointment.date, hour_minute AS time FROM (appointment, menu) WHERE user_id = ? AND appointment.date > ? AND menu.id = style_id ORDER BY appointment.date, appointment.hour_minute;", session["user_id"], curr_day)

        # Send info, size of info and render book_in.html
        return render_template("book_out.html", info=info, info_size=len(info))


# Show latest appointments by style to rate
@app.route("/rates", methods=["GET", "POST"])
@login_required
def rates():

    # Rate specific appointment (get input by post)
    if request.method == "POST":

        # Get input
        appoint_id = request.form.get("appoint_id")
        rate = request.form.get("rate")

        # Check format of input
        result = check_inputs(integer=[appoint_id, rate])
        if not result == None:
            return apology(result, 400)

        # Checks if given appointment exist and, if so, if it belongs to the current user
        validat_info = db.execute("SELECT user_id, rate_id FROM appointment WHERE id = ?", appoint_id)
        if not validat_info:
            return apology("Appointment not founded", 400)
        if not validat_info[0]["user_id"] == session["user_id"]:
            return apology("Appointment is not from this user", 400)

        # Check for valid rate
        rate = int(rate)
        if not (rate > 0 and rate <= 5):
            return apology("Invalid rate", 400)

        # If rate already exists
        if validat_info[0]["rate_id"]:

            # Update existing rate
            db.execute("UPDATE rates SET rate = ? WHERE id = ?;", rate, validat_info[0]["rate_id"])
            # Return message
            flash("Rate updated")

        # If new rate rate
        else:

            # Create new rate
            rate_id = db.execute("INSERT INTO rates (rate) VALUES (?)", rate)
            # Update appointment with new rate
            db.execute("UPDATE appointment SET rate_id = ? WHERE id = ?", rate_id, appoint_id)
            # Return message
            flash("Appointment rated")

        # Redirect to main page
        return redirect("/")

    # If not through post (get)
    else:

        # Get today's date, hour and minute and transform into a float [Y-M-D H:M = int(YMD) + int(HM) / 2400]
        date_now = datetime.now(timezone("Europe/Lisbon")).strftime('%Y%m%d%H%M')
        date_now = int(date_now[0:8]) + int(date_now[8:12]) / 2400.0

        # Get latest appointments from user by style (rated or not rated)
        # info = db.execute("SELECT MAX(CAST(REPLACE(appointment.date, '-', '') AS decimal) + (appointment.hour_minute + menu.time) / 24.0) AS max, menu.name AS name, appointment.id, appointment.rate_id, appointment.date, appointment.hour_minute AS time FROM (appointment, menu) WHERE user_id = ? AND menu.id = appointment.style_id AND CAST(REPLACE(appointment.date, '-', '') AS decimal) + appointment.hour_minute / 24.0 <= ? GROUP BY appointment.style_id ORDER BY appointment.style_id;", session["user_id"], date_now)
        info = db.execute("SELECT MAX(CAST(REPLACE(appointment.date, '-', '') AS decimal) + (appointment.hour_minute + menu.time) / 24.0) AS max, menu.name AS name, appointment.id,  appointment.date, appointment.hour_minute AS time, rates.rate, appointment.rate_id FROM((appointment LEFT JOIN rates ON appointment.rate_id=rates.id), menu) WHERE user_id = ? AND menu.id = appointment.style_id AND CAST(REPLACE(appointment.date, '-', '') AS decimal) + appointment.hour_minute / 24.0 <= ? GROUP BY appointment.style_id ORDER BY appointment.style_id", session["user_id"], date_now)

        # Send info and render rates.html
        return render_template("rates.html", info=info, rates_name=RATES_NAMES)


# Log user in
@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # Procces of login (get input by post)
    if request.method == "POST":

        # Get input
        username = request.form.get("username")
        password = request.form.get("password")

        # Check format of input
        result = check_inputs(username, password)
        if not result == None:
            return apology(result, 400)

        # Get info about username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to main page
        return redirect("/")

    # If not through post (get)
    else:

        # render login.html
        return render_template("login.html")


# Log user out
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Register user
@app.route("/register", methods=["GET", "POST"])
def register():

    # Register potencial user (get input by post)
    if request.method == "POST":

        # Get input
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        number = request.form.get("number")

        # Check format of input
        result = check_inputs(number, username=username, password=password, conf_password=confirmation, email=email)
        if not result == None:
            return apology(result, 400)

        # Store if given username already exist (we are like "creating a function" here and test it)
        has_username = not db.execute("SELECT COUNT(*) FROM users WHERE username = ?", username)[0]["COUNT(*)"] == 0
        if has_username:
            return apology("Username already exist", 400)

        # Insert info about new user in database and get his unique ID
        session["user_id"] = db.execute("INSERT INTO users (username, hash, email, number) VALUES(?, ?, ?, ?)", username, generate_password_hash(password), email, number)

        # Send an email to show that user has been registered
        message = Message("You are registered!", recipients=[email])
        message.html = render_template("register_email.html", name=username, password=password, number=number)
        mail.send(message)

        # Redirect user to home page
        return redirect("/")

    # If not through post (get)
    else:

        # render register.html
        return render_template("register.html")


# Change password being logged or not (with some requirements if so)
@app.route("/password", methods=["GET", "POST"])
def password():

    ## User is logged in
    if 'user_id' in session.keys():

        # Process of change password (get input by post)
        if request.method == "POST":

            # Get input
            new_password = request.form.get("new_password")
            confirmation = request.form.get("confirmation")

            # Check format of input
            result = check_inputs(password=new_password, conf_password=confirmation)
            if not result == None:
                return apology(result, 400)

            # Update password from current user
            db.execute("UPDATE users SET hash = ? WHERE id = ?;", generate_password_hash(new_password), session["user_id"])

            # redirect to main page
            flash("Password changed successfully")
            return redirect("/")

        ## User is logged in
        # If not through post (get)
        else:

            # render new_password.html
            return render_template("new_password.html")

    ## User not logged in
    # Process of generating new password (will be send by user's email) (get input by post)
    if request.method == "POST":

        # Get input
        username = request.form.get("username")
        email = request.form.get("email")

        # Check format of input
        result = check_inputs(username=username, email=email)
        if not result == None:
            return apology(result, 400)

        # Get info about user through username
        info_user = db.execute("SELECT id, email FROM users WHERE username = ?", username)

        # Check if username exist or, if so, email from username match with given email
        if not info_user:
            return apology("Invalid Username", 400)
        if not info_user[0]["email"] == email:
            return apology("Invalid Mail", 400)

        # Generate new password and check it, for security
        new_password = generate_random_password()
        result = check_inputs(password=new_password)
        if not result == None:
            return apology(result + " (Something went wrong while generating the new password, sorry :(. Please try again)", 400)

        # Update user password with generated password
        db.execute("UPDATE users SET hash = ? WHERE id = ?;", generate_password_hash(new_password), info_user[0]["id"])

        # Send new password by email
        message = Message("New Password", recipients=[email])
        message.html = render_template("paassword_email.html", name=username, password=new_password)
        mail.send(message)

        # Render passworded.html
        return render_template("passworded.html")

    ## User not logged in
    # If not through post (get)
    else:

        # Render forgot_password.html
        return render_template("forgot_password.html")


# Change email
@app.route("/email", methods=["GET", "POST"])
@login_required
def email():

    # Process of changing email (get input by post)
    if request.method == "POST":

        # Get input
        email = request.form.get("email")

        # Check input format
        result = check_inputs(email=email)
        if not result == None:
            return apology(result, 400)

        info = db.execute("SELECT username, email FROM users WHERE id = ?;", session["user_id"])
        if info[0]["email"] == email:
            return apology("Same email", 400)

        # Update user email
        db.execute("UPDATE users SET email = ? WHERE id = ?;", email, session["user_id"])

        # Send an email to show that user has been registered
        message = Message("Email chenged!", recipients=[email])
        message.html = render_template("email_email.html", name=info[0]["username"])
        mail.send(message)

        # redirect to main page
        flash("Email changed successfully")
        return redirect("/")

    # If not through post (get)
    else:

        # render email.html
        return render_template("email.html")


# Change number
@app.route("/number", methods=["GET", "POST"])
@login_required
def number():

    # Process of changing number (get input by post)
    if request.method == "POST":

        # Get input
        number = request.form.get("number")

        # Check input format
        result = check_inputs(number)
        if not result == None:
            return apology(result, 400)

        # Update number from current user
        db.execute("UPDATE users SET number = ? WHERE id = ?;", number, session["user_id"])

        # redirect to the main page
        flash("Number changed successfully")
        return redirect("/")

    # If not through post (get)
    else:

        # render number.html
        return render_template("number.html")



'''

pip install flask_mail
pip install pytz
pip install inflect


'''
