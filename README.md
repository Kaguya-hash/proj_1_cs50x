### Project Name: *HAIR Style*
<br>

# Basic Description:

### What a user can "do" on this website:
On this website, users can book appointments about hair styles, unbook them and rate the last appointment that he has, by the type of appointment.

They have also to create an account with their email, username, phone number, and password.

Then, when the user is log in, they can change the password, the email (not the same email), and the number. If a user forgets his password, he can also change it by inputting their username and corresponding email. A newly generated password will be sent to his email. Then, if the user wants, he can change it again when the user is logged in.

### What a user can "see" on this website:
The user has access to the menu (name of each appointment, price, duration, rate (if at least one person rated it)), his next appointment (if it exists), and the available times for a specific type of appointment given by the user, as well as the days he wants to see the available times.

### [HERE](https://youtu.be/4_Lcy70YtzQ) is a video exploring the website
<br>

# Code Description:

We need some configurations for this website, like packages already install (like *Flask_mail* or *inflect*) or environment variables. My initial plan has to write commands to set these configurations in /.bash_profile, but, for example, when there is an update everything seems to go back to the default configuration, and I understand that. Due to the uncertainty of something bad can happen, I decided of putting these commands in *scriptset.sh*. So there is just the need to do the *source scriptset.sh* like in the following example:
```bash
source scriptset.sh
```
This will execute all the commands inside to make sure everything is set (there is some code to see if some things are already set)

Here we will use the configuration of *flask* (python) so we will need to have an application.py (app.py), templates (folder with .html files), static content (folder with CSS files to style templates, for example, and images to also style, etc), requirements.txt (libs used in app.py) and other stuff to help in various ways (flask_sessions to session, info.db (database), README.md (this file, to instructions), etc).

Resume of which file:
  - **info.db** (database): here we just store info about users, appointments, and other things.
  - **flask_session**: this folder stores info about the user's cookies.
  - **templates**: a folder that stores templates to be displayed on the user side.
  - **static**: folder with CSS files and images to be used in templates.
  - **app.py** (python): a bridge between the user input and the database, gives output to the user using different algorithms and functions depending on the user's request.
  - **helpers.py** (python): resources that are included in app.py, with functions for example.
  - **scrptse.sh**: commands to be executed before running the website (with the "source scrptse.sh" command).
  - **date.txt**: stores a date, used to update the database (can be edited by the program).
  - **requirements.txt**: has the libraries requested by app.py (flask configurations)

## **Info.db:**

This basic database file (SQLite) has various tables:

##### **Users**
  - An unique id that autoincrements when a user is added
  - An unique username (text not null)
  - A hash (password) (text not null)
  - An email (text not null)
  - A phone number (text not null)

##### **Menu**
  - A id for each type of appointment (autoincrement for future addictions or deletions)
  - name of type (text not null)
  - price (number not null)
  - duration (time) (number not null)
  - a rate (integer between 0 and 5) that can be updated

##### **Rates**
  - An unique id that autoincrements when a rate is added
  - rate (number)

##### **Appointment**
  - An unique id that autoincrements when an appointment is added
  - user id (a reference to users.id) (number not null)
  - style id (reference to menu.id) (number not null)
  - rate id (reference to rates.id) (number not null)
  - date (date not null)
  - time (hour_minute) (real not null) (Xh:Ym = X,Y)

It has also indexs for users.id, appointment.id, rates.id, users.username and appointment.date.
Other tables or columns of certain tables are not used either because their purpose is just to store info (and not to use it as a "navigator" through some info needed) or because it's just not worth it because of space consumption (for example, as we will see in app.py, to find appointments.time we first select dates and per each date, there are not many appointments, so it's not worth it to create an index for time, in case we need a certain time or range of times of course).

## **App.py:**

First, we import various libs (like helpers.py, stored in this folder).

Then we have the configurations.
We start be create an *app* with **Flask()** and add configurations to the email, added to the *mail* variable with **Mail()**. This email was also enabled to send emails using a specific password. Also, we use **os.environ** to get variables of the environment.
Then we set *True* to ensure templates are auto_reloaded.
**app.jinja_env.filters** is used to "pass some functions" to be used in.html files (through jinja code).
We also configured sessions not to be permanent, just while the user is interacting with the website (*filesystem*).
Then an object is created to manipulate info in info.db later, using **SQL()**.

Note: each of them (funcitons) will have a decorator that will execute the below function depending on the user request (it can be after a request, **@app.after_request**, or to a "link" (request), **@app.route("/book_out", methods=["GET", "POST"])**).
Also, we create a decorator called **login_required** that sees if a user can have the results of his request, just if he is logged in (stored in helpers.py).

  - **after_request(response)**: Here we just ensure that responses aren't cached, following configurations. This function is "activated" after a request.
  - **index()**: First, we store info about the menu in *info*. Then we get two types of formats to the present time ([yyyy-mm-dd] and [yyyymmdd + (hhmm / 2400.0)], as a float). Then we get "when" it was the last update (stored in form of time (yyyy-mm-dd hh:mm)), and if it doesn't match today's date, we will have to update the rates of each style in a *for loop*. For each style:
    - Select the list of the latest rated appointments of that style from every user
    - If we have at least one rate, calculate the average with **avg_list()** and stored it in the database and *info*, to send it to the user interface.
    - Then get the current time in the form 'yyyy-mm-dd hh:mm', and store it in date.txt (by re-write it with that info).
  Then we select the nearest appointment from the user requesting information if it exists.
  Return the page with the necessary information.
  - **book_in()**: There are two types of request here:
    - methods = GET: select info about the menu, the tomorrow date, and return this info.
    - methods = POST: get input from the user and check it (with a return message for what goes wrong). Then check if the times are correct (*data_from* needs to be after today's date and *data_to* bigger or equal then *data_from*). Select info from the requested style (from the menu and its existence). Get instances from the class **date** using the dates given by the user.
    Then, for each day, do the following:
      - Get appointments from that day from that user
      - Find available spaces in that day, given the appointment duration, using **find_spaces()** (helpers.py). It will give a list of the list with the starting time first and then the ending time.
      - If it has any spaces, store in info in a form of a list of size three, first with the list of available spaces, then the day being analyzed and a distinct number (distance between the day being analyzed and the first day being analyzed). This last information (number) will be used then in a .html file to facilitate the creation of tables.
    In the end, we just render "book_in_available" with the necessary info.
  - **book_in_validation()**: Here the only request is through POST, so we have to check it. Then we get the input from the user and test their forms. Convert the given time into a float with **time_to_float** (helpers.py) (hh:mm = hh + (mm / 60)). Get info duration and name of giving style, and test its existence.
  Now we will verify if we can schedule the given appointment, with the given information by the user.
  First, we get info about appointments on the chosen day, but the time of the chosen appointments has to be between the requested time minus two (max. duration of an appointment) and the requested time plus the duration of the requested appointment. Then we check if it is a valid time with **valid_time()**, given the list of appointments (really similar to the **find_spaces()** function), the time and duration of the appointment (helpers.py). After that insert the new appointment.
  Now we want to send an email to the user.
  We start by getting some info about the user. Then create a **Message** instance (*message*), give it some info (like the email to be sent), some .html to present to the user info about his new appointment ("in_email.html", with his name and duration, time and day of the new appointment). Then, finally, we send it.
  Lastly, flash a successful message and redirect to the main page ("/").
  - **book_out()**: There are two types of request here:
    - methods = GET: get today's date in form of a string and get info about appointments that will occur after today's date (user cannot mark off today's appointments). Then render "book_out.html" with this info (code in "book_out.html" will organize this info).
    - methods = POST: get info and test it's form. Get info about this appointment to be marked off,  if it exists (return apology if not). Also, check if this appointment belongs to the user that wants to mark it off (return apology if not). Delete the given appointment. Then we send an email to the user in a very similar way in **book_in_validation()**, but we give "out_email.html" and info about the user name and name, date and time of the appointment being marked off, instead.
    Flash a successful message and redirect to the main page.
  - **rates()**: There are two types of requests here:
    - methods = GET: get current time in a certain form (float): yyyymmdd + hhmm / 2400 .
    Then, we will get a list of the latest appointments (rated or not) from each appointment_style from the user requesting this info (completed appointments before the current time) .
    At last, render "rates.html" with the given list and *RATES_NAMES*, which is a dict where the keys are values between 1 and 5 (rate numbers) and the info attached to the keys are expressions associated with the numbers (Example: 2 = "Poor") (stored in heplers.py) .
    - methods = POST: get input and test their forms. Then, get info about the appointment given by the user, if it exists (return apology if not), and see if it belongs to the user requesting. Check if the rate is valid, between 1 and 5, inclusive.
    Then we have two paths:
      - appointment already rated: then, we just update the rate of that rate, and store it in the **rates** table in the database. Lastly, flash a successful message.
      - appointment not rated: create a new rate in the rates table and
  - **login()**: first we clear anything that the session may have we log out of any user.
  Then, there are two types of requests here:
    - methods = GET: just render the "login.html" file
    - methods = POST: get input and test their form. Then get info about the user with the given *username*. Now, we will test if it exists and if the password in the database matches the given password. If every input is right, create the session with the user id and redirect him to the main page ("/").
  - **logout()**: Here, the function just gets rid of the session, like in login at the beginning, and then redirects to the main page ("/").
  - **register()**: There are two types of requests here:
    - methods = GET: render "register.html"
    - methods = POST: get input and test their forms.
    Then check if the given username already exists. Then insert the various given values (username, password (hashed), email, number).
    Then we send an email to the user in a very similar way in **book_in_validation()**, but we give "register_email.html" and info about the username, password and number, instead, given by the user.
    Then the user is redirected to the main page
  - **password()**: Here the user can request whether this URL is being logged in or not. So we will have two options:
    - User is logged in: There are two types of requests here:
      - methods = GET: just render "new_password.html"
      - methods = POST: get input and test their forms. Just hash the password and update it in the database, from this user.
      Flash a successful message and redirect to the main page.
    - User is logged out:
    There are two types of requests here:
      - methods = GET: just render "forgot_password.html"
      - methods = POST: get input and test their forms.
      Get info from the user with the given *username*. If it does not exist or if the email from that user is not equal to the given email, return an apology.
      Now we create a new password for the user using **generate_random_password()** (helpers.py) and test it, just for security. Now, with everything created, the password from the user (user given by the *username* given by the "web user") will be updated.
      Then we send an email to the user in a very similar way in **book_in_validation()**, but we give "password_email.html" and info about the username and the new password, instead, because the user has to somehow.
      Finally, we just render "password.html".
  - **email()**: There are two types of requests here:
      - methods = GET: just render "email.html"
      - methods = POST: get input and test their forms.
      Get info from current users on the site. If the new email is equal to the already registered one, return apology.
      If not, update the email with the new email in the database.
      Then we send an email to the user in a very similar way in **book_in_validation()**, but we give "email_email.html" and info about the username instead.
      Finally, we flash a successful message and redirect the web user to the main page ("/").
  - **number()**: There are two types of requests here:
      - methods = GET: just render "number.html"
      - methods = POST: get input and test their forms.
      Then, change the number in the database from the web user.
      Lastly, flash a successful message and redirect to the main page ("/").

## **Helpers.py:**

First, we import various libs.

Then we define various constants, like the hour of various important times of the day (*START_OF_LUNCH*, *END_OF_LUNCH*, etc (#12-#15)), *MAX_DURATION_APPOINTMENT* that stores the max. hours that an appointment can have and *RATES_NAMES* to convert numbers in sentences when a rate is presented in an HTML file (or vice-versa).

Now we start the functions:
  - **apology(message, code=400)**: First, a function **escape(s)** is created (#24): this function will replace certain characters with others (#29-#31) because the *s* (a string) will be applied in a link, and certain characters have to be replaced (example: if we want to right "%" in a link, instead we have to put a "~p", that then will mean a "%"). Then we return the "mutated string".
  Finally, we render the "apology.html" with info about the "mutated *message*" (filtered by the **escape(s)** function), and the *code*, which will be 400 by default.
  We will also give *code*, to pass "how the request has been received" (400, something is wrong with inputs, or 500 for an internal problem (although we don't want that kind of error))
  - **login_required(f)**: First we create a function, **decorated_function(\*args, \*\*kwargs)** (#42) that will serve as a decorator,  @wraps(f) (f is the function next to the decorator) (#41): this "inside function" will test if someone is log in, by checking the *session["user_id"]* (#43). If doesn't exist, redirect to "/login". Else, return the function, that will be executed. Lastly, we return this created function (decorator)
  - **usd(value)**: just format the *value* (float) and return it in a string format ("$(value with two decimal places)")
  - **time(value)**: take a values (float) and format it to a specific string. Example: uu.dd = "uu(with two units):dd*60(with two units, rounded)"
  - **heading_number(value)**: values (integer) to a specific string. Example: *value*=2, then: "headingTwo" (we transform the number into a string (its name))
  - **collapse_number(value)**: values (integer) to a specific string. Example: *value*=2, then: "collapseTwo" (we transform the number into a string (its name))
  - **hash_collapse_number(value)**: values (integer) to a specific string. Example: *value*=2, then: "#collapseTwo" (we transform the number into a string (its name))
  - **time_to_float(time)**: Converts a *time*, string with format="HH:MM", and converts into a float. "HH:MM" -> hh + mm / 60.0
  - **rate_to_name(rate)**: Takes a *rate* (float) and transforms it into a string. Example: 3.42 -> *RATES_NAMES[3]* (3.4) (rates)
  - **find_spaces(info, duration)**: tries to find a set (sorted by the starting number) of ranges with a size bigger than *duration*, given a list (sorted by the starting number) that doesn't intercept and never have numbers smaller than *START_OF_SERVICE* (8) and bigger than the *END_OF_SERVICE* (20) and never have numbers between the *START_OF_LUNCH* (12) and *END_OF_LUNCH* (14):
    - first, we create an empty *list* (#95) and an *index* (#96) (to follow the list while being analyzed, will be useful).
    - then create a *mark* (#99), to follow "when we are" (will be useful to create the math ranges and other things).
    - then we start a for loop that will iterate through the appointments (orderly). Will run until something stops it (#101):
      - stop condition: if the time of appointment being analyzed is bigger than *START_OF_LUNCH* (12) (#104), break the loop (#105).
      - if the time between the *mark* and the math range being analyzed is equal to or bigger than the *duration* (#108), add a math range (in a list form, with two numbers, the starting and ending numbers of the closed math range) that begins at *mark* and ends at the beginning of the math range being analyzed (#109) to the *list*.
      - update *mark* to be at the end of the next range (#112)
      - increase the index by one (to follow the current math range in the list) (#113)
    - Check if the range with a size *START_OF_LUNCH* - *mark* is bigger than *duration* (#116). If it is, add a math range that begins at *mark* and ends at *START_OF_LUNCH* (#117) to the *list*. We have to do this to make sure no one marks something at lunch and we can see if there is a space between the last math range before the *START_OF_LUNCH* and the *START_OF_LUNCH*.
    - update the *mark* to *END_OF_LUNCH* (#120)
    - then we start a for loop very similar to the first loop (#122). The difference is that it will not need the index (because the purpose of the index was to continue where the other for loop left the list *info* (#122)) and it will go until there are no math ranges in *info* to be analyzed (there is no stopping point inside of this for loop).
    - Check if the range with a size *END_OF_SERVICE* - *mark* is bigger than *duration* (#132). If it is, add a math range that begins at *mark* and ends at *END_OF_SERVICE* (#133) to the *list*. We have to do this so we can check if there is a space between the last math range before the *END_OF_SERVICE* and the *END_OF_SERVICE*.
    - Lastly, we return the *list*.
  - **valid_time(info, time, duration)**: Check if a certain math range ([*time*, *time* + *duration*]) does not intercept a list, *info*, that has math ranges (sorted by the starting number) that don't intercept and just can have numbers between *time* - *MAX_DURATION_APPOINTMENT* and *time* + *duration* (we do this because, in this specific case, we just want to analyze the appointments near the appointment to be added).
    - First, we check if the math range [*time*, *time* + *duration*] doesn't come before *START_OF_SERVICE* or after *END_OF_SERVICE* and doesn't intercept [*START_OF_LUNCH*, *END_OF_LUNCH*] (#143).
    - Start a loop that will iterate through the given *info* of math ranges (#147):
      - if the starting number of the math range being analyzed is smaller that *time* (#150):
      if the ending number of the math range being analyzed comes after *time* (#151), return false.
      - Else (#155):
      if the ending number of the math range [*time*, *time* + *duration*] comes after the starting number of the math range being analyzed (#156), return false.
    - If nothing went "wrong" until now (return false), return true (#160).
  - **check_inputs(\*args, \*\*kwargs)**: *args* (like a list) will take various independent variables and *kwargs* (like a dict) will take lists of variables or just single variables identified by a key. When there is an error in some format, it gives us a string saying what possibly went wrong. If everything goes right, it gives us *None*. The variables are all strings.
  First, check if elements from *args* (#168) have something (not "NULL") (#169) and if they are not too big (size of str in bigger than 40) (#171).
  Do the same for *kwargs* (#175). However, here (and first), check if the *kwargs[key]* is a list (#176): if so, check each element from that list (#177), also in a similar way to the first for loop of this function.
  Store a standard beginning of an error string, from now on (#188).
  Then, there are specific checks for each key in kwargs, if they exist:
    - email type (#191) (cannot be a list): check for the "@gmail.com" format at the end of the string and check if there is just one word (#193).
    - username type (#198) (cannot be a list): checks for a string with just one word and size smaller than 20 (#200)
    - password type (#205) checks for just one word and if size >= 8 and <= 20. Also, checks for numbers, capital letters and small letters (we just order the letters and check "number(s)/capital_letter(s)/small_letter(s)") (#209).
    Also, if there is a "conf_password" in the keys of *kwargs* (#214), check if it is equal to kwargs["password"] (#216).
    - dates type (#220) (has to be a list): for each string in *kwargs["dates"]*, check for the exact format: "four_integers-two_integers-two_integers". Then check if the given date is, in fact, a valid date (#227).
    - integer type (#228) (needs to be a list): check if it is a string of digits (#235)
    - time type (#235) (cannot be a list): check for the exact format: "two_integers:two_integers". Then, we will if the given time is a valid time with just "00", "15", "30", and "45". Start by transforming the given *time* into a float and multiply it by 4. Just if the minutes are "00", "15", "30", "45", the output will be an integer (#251). Also has to be smaller than 24 * 4 (the days just have 24 hours). Proof that this works:
      - (=>) It's trivial that if we have the right format, it will give us an integer number
      - (<=) Let's assume it gives us an integer number and divide it by 2. It can give us:
        - integer (even). Divide again by 2. It can give us:
          - integer (even)
          - integer.5 (odd)
        - integer.5 (odd). Divide again by 2. It can give us:
          - integer.25 (even)
          - integer.75 (odd)
      - So we will always have .00, .25, .50, .75, which is "00", "15", "30", "45".
  - **generate_random_password()**: first we make a list of all ascii_letters + digits and shuffle it (#263, #264). Then choose 8-10 numbers for the *password* list (size is randomly chosen) (#268). Shuffle the *password* again (#272). Then add to that string a random capital letter, a random small letter, and a random digit (#275). Lastly, return it.
  - **avg_list(list, key)**: **key()** will be a function that transforms an object into a real number. This simple function just adds all the objects (transformed into numbers by the **key()** function) and then divides it by the number of numbers added (average).

## **Requirements.txt:**

Here we simply declare the libs imported to the application.py (app.py).

## **scriptset.sh**

This file has some commands to be executed (through *source scriptset.sh*) that provide packages and necessary environmental variables to this program.
There are *if* statements that check if certain variables already exist (#1, #7, #13). If they are not, we create them with values (#3, #9, #15). We also install some packages (#21-#23) if they don't already exist.

## **Date.txt:**

This .txt file has the last time when the website updated the rates of each style of appointment.

## **Templates (folder):**

Here, we have two main layouts:

  - signature.html. This .html will have a <*main*> block to be completed by other files that extend this file.
  Files that extend it:
    - register_email.html: confirms the registration of the user, and displays/uses his *name*, *number*, and *password* as variables given by app.py.
    - paassword_email.html: gives the newly created password, and displays/uses the user *name*, the new *password*, given by app.py.
    - out_email.html: confirms deletion of appointment of the user, and displays/uses his *name*, *style*, *date*, and *time* of the appointment as variables given by app.py.
    - in_email.html: confirms new appointment of the user, and displays/uses his *name*, *style*, *date*, and *time* of the appointment as variables given by app.py.
    - email_email.html: confirms new email and displays/uses his *name* as a variable given by app.py.
  - layout.html. First, in <*head*>, set a flexible display and get some <*link*>'s and <*script*> from bootstrap and styles.css, as well as an icon to be displayed in the tab of the page. Also, a title is added to the website tab, with a block <*title*> to be completed by an unknown .html file that would extend this layout.html.
  Then, in <*body*>, we have, first, <*nav*>. This is all configured by bootstrap, but the section that maybe it's interesting to explain is from the *if* (#37) to the *endif* (#52). Here, if there is a session (user is log in), display links to "/book_in", "/book_out", "/rates" and "/logout". Else (user log out), display links to "/register" and "/login". This will be the end of <*nav*>. Next, we have a <*header*>, that just displays a message given by app.py when it exists. End of the <*header*>. Lastly, we have the <*main*> that displays a block given by the .html file that extends this .html file.
  Files that extend it:
  <br>Note_1: in all files represented below, we start by adding a specific sentence in the title.
  <br>Note_2: Everytime there is, for example, a variable representing time or money, we will transform it via **time()** or **usd()** functions. This can happen with other variables if they need to be transformed. The functions we use are: **usd()**, **time()**, **heading_number()**, **collapse_number()**, **hash_collapse_number()** and **rate_to_name()** (helpers.py).
    - apology.html: just outputs a message in form of an image with a certain configuration given by app.py through *top* and *bottom* (can be transformed by **urlencode()** function)
    - book_in_available.html: in block_main, first in outputs an header (<*p*>) (#12) with the style name (*style_info["name"]*) and the style duration (*style_info["duration"]*).
    Then, by each day (#18), we create a dynamic, that needs some info to work (*day[2]*, which stores the number that represents the relative numbering of the day, needed by the configuration of bootstrap). Inside this "fluid table", we create a proper table. To this table (representing a day), we put, by each column, the *available* times by putting the start_time (*available[0]*), ending_time (*available[1] - style_info["duration"]*) and some inputs to be completed (or hidden), to then send to this URL via POST, like the *style_id* or the given *time*.
    - book_in.html: it shows when you can schedule your appointment with *date*.
    Then, there is a form that takes you to this URL with the method POST. If we go this way, we have to select a style (presented as an option, the info about style is given by app.py with *info*). Also, we have to give a *date_from* and a *date_to* (starting date and ending date, respectively).
    - book_out.html: here we show tables (each one of them represents a day) with the user's future appointments (except today).
    The reason why *info* is not separated by dates, for example, to be easiest to create the tables is because, in this way, we can iterate through *info* just one time, instead of two (and because is cooler XD).
    So, in block *main*, if there are no appointments (#12), we present a message (#15).
    Else, we will iterate through *info*, accessing it with index *i* (#20). In each scan of a certain *info[i]* (appointments) we will do the following:
      - if i == 0, beginning of the for loop (#23), a table is created by putting the date of *info[i]* (*info[i]["date"]*) and other configurations.
      Else, if the date from the previous appointment is different from the appointments being analyzed (#38), that means we just end the appointments from the previous appointment date, so the previous table has to be closed and a new one has to be created, with its date (*info[i]["date"]*) and, again, some configurations.
      - (#60) output a row of info about this appointment, like *info[i]["time"]*, *info[i]["duration"]* and *info[i]["name"]*. Also, there is the need for a form that POSTs to this URL with the click of a button, that sends the id of the appointment to be marked off.
      - if we are at the end of *info* (#74), we close the previous table.
    - email.html: here you just have a form that takes us, be POST, to this URL with info about the new *email*
    - forgot_password.html: here we just submit a form by POST to this URL, with the *username* and the *email* from the user.
    - login.html: here we just submit a form by POST to this URL, with the *username* and *password* from the user.
    Also, there is a link to "/password" (if the user forgets the password)
    - new_password.html: here we just submit a form by POST to this URL, with the *new_password* and the *confirmation*.
    - number.html: here we just submit a form by POST to this URL, with the *number*.
    - passworded.html: just presents a message saying that the new password is the user's email
    - portfolio.html: here, the menu is presented to the user in a table with various information about each appointment style, like the name, duration, price, and rate, all stored in *info* and displayed with a for loop (#23). The date of the last update is also presented (should be the day the user is checking this page, but not necessarily the time. The only user who will have the privilege (obviously a privilege of seeing the exact current day and time XD), is the first user accessing the site, details in app.py).
    Also, if there is a next appointment (#36) (if not presented a message instead (#47)), it presented its date, time, duration, and type of appointment.
    There are also links to change the password, email, and number ("/password", "/email" and "/number").
    - rates.html: here is presented a table of appointments (last appointments from each style, from this user) to be rated, again if the user already rate it.
    The information is stored in *info* and displayed in a for loop (#22).
    In each column the date, time and name are presented.
    It also presented the appointment rate, if it was already rated by the user (#29).
    Finally, we have a form that takes us by POST to this URL. Inside, we have all the possible rates, stored in *rates_name* and presented in a for loop (#34).
    The id of the appointment (*appoint["id"]*) is also sent
    - register.html: here, there is a form that takes the user by POST to this URL.
    Inside it, the user has to put his *username*, *email*, *number*, *password*, and *confirmation*, following the given rules.

## **Static (folder):**

In this folder we have:
  - styles.css: some code to style some classes and tags
  - hair.ico: used to put a picture in the tab of the website

## **Flask_session (folder):**

This folder is just used to store the "keys" (sessions) that the user is supposed to have in his "machine" (or not if the user is not logged in while searching through the site)

# Final note:

There are already a lot of data in the database, but I will not delete it because it's just not necessary.

To be honest, there are many things that i regret not doing in this project.<br>
For example, the time and date are stored separatetly, but i could store them both in just one row and with a number so that it would be not necessary to do that aplication from an object (with two specific types of strings) to a real number:<br>

$$ f(\{ appointment.date, appointment.hourminute \}) = $$
$$ = CAST(REPLACE(appointment.date, '-', '') \ AS \ DECIMAL) + appointment.hourminute / 24.0) \in \mathbb{R} $$

It would be easily done to transform a string into a list of integers and then into a single float (or another integer). Everything without losing information and winning time, organization, and space, which can be critical.

I would love to implement some code to deal with race conditions but, for some reason, I couldn't install some necessary packages to do that.

Unfortunately, I had to stop adding these little "more efficient" things due to lack of time (i am studying mathematics, so exams and projects are starting to pop up).

However, I'm proud of this and even more proud to know what I could have done better, so that next time I don't do the same mistakes.<br><br><br>

## By the way
-----------------
[HERE](https://www.youtube.com/watch?v=xvFZjo5PgG0) is the video that inspired me to do this site about hair