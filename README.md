# HAIR Style

A Flask-powered salon booking app built for appointment scheduling, user account management, and service ratings.

## What this repo shows
- user registration and login
- booking and canceling salon appointments
- viewing available slots by service and date range
- rating completed appointments
- account updates for email, phone, and password
- HTML email notifications from the app

## Important deployment note
This `main` branch keeps mail configuration hidden and does not expose local email credentials.

⚠️ The other branch, `mail-rework`, contains full email configuration and supports password reset, booking confirmation, cancellation notices, and other mail flows. It works locally when you run it with the right env vars, but on Render Gmail/SMTP restrictions may still affect delivery.

## Live demo
Visit the running site on Render:

https://proj-1-cs50x.onrender.com/

## Local usage
This branch is intended to describe the app and its features. For a local run, use the `app.py` Flask app and the provided dependencies.

## Tech stack
- Python 3
- Flask
- Flask-Mail
- Flask-Session
- SQLite
- Jinja2 templates
- Dotenv for config
