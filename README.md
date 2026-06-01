# HAIR Style

A Flask-based salon booking app with account management, appointment scheduling, cancellation, ratings, and email notifications.

## What it does
- User registration and login
- Book and cancel hair appointments
- View available time slots by service and date range
- Rate completed appointments
- Update account email, phone, and password
- Send confirmation emails for registration, bookings, cancellations, and password resets

## Why it matters
This project demonstrates a complete user flow for a service-oriented web app:
- secure login and session management
- SQLite-backed appointment logic
- dynamic availability search
- email integration using Flask-Mail
- clean MVC-style Flask templates

## Run locally
1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
# or on Windows PowerShell:
# .\venv\Scripts\Activate.ps1
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set Flask and mail environment variables
 > ⚠️ **Important Note:** These credentials belong to a temporary, experimental email used for development. Hardcoding secrets isn't best practice for production, but it's fine for this demo.

```bash
export FLASK_APP=app.py
export MAIL_DEFAULT_SENDER=mybarbershopapp39@gmail.com
export MAIL_USERNAME=mybarbershopapp39@gmail.com
export MAIL_PASSWORD=dxrtfiwcqqjyzvxg
```

4. Start the app

```bash
flask run
```

5. Open `http://127.0.0.1:5000`

## Notes
- The app uses `info.db` as its local SQLite database.
- Templates are in `templates/` and styles are in `static/styles.css`.
- Email settings are configured for Gmail SMTP.

## Quick tech summary
- Python 3
- Flask
- Flask-Session
- Flask-Mail
- CS50 SQL wrapper
- SQLite
- Jinja2 templates
- dotenv for local config
