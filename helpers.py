import re

from flask import redirect, render_template, request, session
from functools import wraps
from secrets import choice
from string import ascii_letters, digits
from random import shuffle
from inflect import engine
from datetime import datetime

# Definition of various important times in the day, designate number values (hour) to each "day event"
START_OF_LUNCH = 12
END_OF_LUNCH = 14
START_OF_SERVICE = 8
END_OF_SERVICE = 20

# Max. duration of an appointment
MAX_DURATION_APPOINTMENT = 2

# List for rates
RATES_NAMES = {1: "Very bad", 2: "Poor", 3: "Ok", 4: "Good", 5: "Excellent"}

# Render message as an apology to user
def apology(message, code=400):

    def escape(s):
        # Escape special characters. https://github.com/jacebrowning/memegen#special-characters
        # Use to not mess with the URL sintax
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    # render with info
    return render_template("apology.html", top=code, bottom=escape(message)), code


# Decorate routes to require login. https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Format value as USD
def usd(value):
    return f"${value:,.2f}"


# Format value as time (float to time)
def time(value):

    hour = int(value)
    minute = int((value - hour) * 60)

    return f"{hour:02d}:{minute:02d}"


# Use to creat diferent tables in html depending on number
def heading_number(value):
    return "heading" + engine().number_to_words(value).capitalize()


# Use to creat diferent tables in html depending on number
def collapse_number(value):
    return "collapse" + engine().number_to_words(value).capitalize()


# Use to creat diferent tables in html depending on number
def hash_collapse_number(value):
    return "#collapse" + engine().number_to_words(value).capitalize()


# Convert time format to float ("H:M" = H + M / 60)
def time_to_float(time):
    return int(time[0:2]) + int(time[3:5]) / 60.0


# Convert number into a rate through list of rates (line 11)
def rate_to_name(rate):
    if rate == None:
        return "--"
    return f"{RATES_NAMES[round(rate)]} ({rate:,.1f})"


# find available spaces in list of appoinments of a day
def find_spaces(info, duration):

    # list to store spaces
    list = []
    index = 0

    # mark = current time being analysed
    mark = START_OF_SERVICE
    # Spaces in the morning
    for appoint in info:

        # End of morning appointments
        if appoint["time"] > START_OF_LUNCH:
            break

        # If space between current time and next appointment bigger than duration of request style, add space
        if appoint["time"] - mark >= duration:
            list.append([mark, appoint["time"]])

        # Current time gets value of end of appointment
        mark = appoint["time"] + appoint["duration"]
        index += 1

    # If there is space until lunch (12h), add it
    if START_OF_LUNCH - mark >= duration:
        list.append([mark, START_OF_LUNCH])

    # Spaces after lunch until end of service (20h) (lunch ends at 14h)
    mark = END_OF_LUNCH
    # Analyses appoints that are after morning appointments
    for appoint in info[index:]:

        # If space between current time and next appointment bigger than duration of request style, add space
        if appoint["time"] - mark >= duration:
            list.append([mark, appoint["time"]])

        # Current time gets value of end of appointment
        mark = appoint["time"] + appoint["duration"]

    # If there is space until end of service (20h), add it
    if mark + duration <= END_OF_SERVICE:
        list.append([mark, END_OF_SERVICE])

    # return info about available spaces
    return list


# Checks if appointment can be schedule in certain day (info has appointment of given day, near the time of appoinment to be schedule)
def valid_time(info, time, duration):

    # Checks if it is not out of service and not in lunch time
    if time > END_OF_SERVICE - duration or time < START_OF_SERVICE or (time < END_OF_LUNCH and time > START_OF_LUNCH - duration):
        return False

    # Checks appointment of that day
    for appoint in info:

        # If it starts before an appointment and ends after it, false
        if appoint["time"] < time:
            if appoint["time"] + appoint["duration"] > time:
                return False

        # If starts after and appointment intesects start of appointment to be schedule, false
        else:
            if time + duration > appoint["time"]:
                return False

    # Else, it's a valid appoinment to be schedule
    return True


# Check format of inputs in general or varius type of inputs (email, username, password, ...)
# Some of the specific types don't take list because it is not required for the purpose of this program
def check_inputs(*args, **kwargs):

    # Checks if unspecified inputs are not None or are not too large
    for elem in args:
        if not elem:
            return "Fill all the input"
        if len(elem) > 40:
            return "Too long input(s)"

    # Checks if specified inputs (elemets or lists) are not None or are not too large
    for key in kwargs:
        if type(kwargs[key]) == type([]):
            for elem in kwargs[key]:
                if not elem:
                    return "Fill all the input"
                if len(elem) > 40:
                    return "Too long input(s)"
        if not kwargs[key] :
            return "Fill all the input"
        if len(kwargs[key]) > 40:
            return "Too long input(s)"

    # Standart beggining for wrong format error
    sentence = "Wrong format for "

    # For email
    if "email" in kwargs.keys():
        # Just one word and ends with "@gmail.com"
        check_email = not (re.search(r'@gmail.com$', kwargs["email"]) == None or len(kwargs["email"].split(" ")) != 1)
        if not check_email:
            return sentence + "email"

    # For username
    if "username" in kwargs.keys():
        # Just one word and less that 20 letters
        check_name = len(kwargs["username"].split(" ")) == 1 and len(kwargs["username"]) < 20
        if not check_name:
            return sentence + "username"

    # For password
    if "password" in kwargs.keys():

        length_pass = len(kwargs["password"])
        # Sorte word, find at least one capital letter, small letter, number, between 8 and 20 characters and just one word
        check_password = not (re.search(r'\d.*?[A-Z].*?[a-z]', ''.join(sorted(kwargs["password"]))) == None or length_pass < 8 or length_pass > 20 or len(kwargs["password"].split(" ")) != 1)
        if not check_password:
            return sentence + "password"

        # For confirmation of given password
        if "conf_password" in kwargs.keys():
            # Check if "password" equal to "confirmation"
            if not kwargs["password"] == kwargs["conf_password"]:
                return "confirmation do not match"

    # For dates
    if "dates" in kwargs.keys():
        for date in kwargs["dates"]:
            # Checks format "yyyy-mm-dd"
            check_date = not re.search(r'^\d\d\d\d-\d\d-\d\d$', date) == None
            if not check_date:
                return sentence + "date(s)"
            try:
                newDate = datetime(int(date[0:4]), int(date[5:7]), int(date[8:]))
            except ValueError:
                return sentence + "date(s) ergsdgdf"

    # For integer
    if "integer" in kwargs.keys():
        # Checks if number is a natural number or zero
        for number in kwargs["integer"]:
            if not number.isdigit():
                return sentence + "integer(s) (something is messing with the style)"

    # For time
    if "time" in kwargs.keys():

        # First checks format "hh:mm"
        check_time = not re.search(r'^\d\d:\d\d$', kwargs["time"]) == None
        if not check_time:
            return sentence + "time(s)"

        # Convert time into float * 4
        time = time_to_float(kwargs["time"]) * 4

        # The time has to be smaller that 24 (so smaller than 24 * 4)
        # And the only float who will produce an integer number will be [.00, .25, .50, .75]
        check_time = time.is_integer() and time < 24 * 4
        if not check_time:
            return sentence + "time(s) (smaller than 24 hours and has to be quarters of an hour)"

    # return None if everything is correct
    return None


# Generats random password
def generate_random_password():

    # List of all ascii_letters + digits shuffled
    characters = list(ascii_letters + digits)
    shuffle(characters)

    # Appends between 8 and 10 random characters
    password = []
    for i in range(choice(range(8, 10))):
        password.append(choice(characters))

    # Shuffle the created password
    shuffle(password)

    # return this password + random upper letter + ramdom lower letter + random digit
    return "".join(password) + choice(ascii_letters).upper() + choice(ascii_letters).lower() + choice(digits)


# Takes a list and finds "average of elements" (F(elem) = number, where F() = key())
def avg_list(list, key):

    # Add all elements to avg
    avg = 0
    for elem in list:
        avg += key(elem)

    # Return some / number of elements in list
    return avg / len(list)