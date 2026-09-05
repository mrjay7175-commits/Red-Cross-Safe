# Deployment Guide

This project runs fine locally with `manage.py runserver`, but that server
is **not safe for production** (Django prints a warning about this on every
start). Here's how to actually put it online.

## 1. Before deploying anywhere

- [ ] Generate a fresh `SECRET_KEY` and put it in an environment variable
      instead of hardcoding it in `Data/settings.py`.
- [ ] Set `DEBUG = False`.
- [ ] Set `ALLOWED_HOSTS = ["yourdomain.com"]` (or the host the platform gives you).
- [ ] Switch `EMAIL_BACKEND` to SMTP (see comment in `settings.py`) if you
      want real emails, not console output.
- [ ] Use a real database in production if you expect concurrent users -
      SQLite (the default here) is fine for a demo/small clinic, but
      Postgres is safer once multiple people use it at once.
- [ ] Run `python manage.py collectstatic` so CSS/JS/images are served
      correctly (the dev server does this automatically; production
      doesn't).

A minimal production-ready settings snippet:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
```

You'll also want a WSGI server instead of `runserver` - `gunicorn` is the
standard choice:

```bash
pip install gunicorn whitenoise
gunicorn Data.wsgi:application
```

`whitenoise` lets Django serve static files itself without a separate
nginx/Apache config - add it to `MIDDLEWARE` (right after
SecurityMiddleware) and set:

```python
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

## 2. Option A - Render.com (free tier, easiest)

1. Push this project to a GitHub repo.
2. On Render: New -> Web Service -> connect your repo.
3. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Start command: `gunicorn Data.wsgi:application`
5. Add environment variables: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` (your `*.onrender.com` URL).
6. Render gives you a free Postgres instance too if you want to move off SQLite - just add `dj-database-url` and point `DATABASES` at the `DATABASE_URL` env var it provides.

## 3. Option B - Railway.app

Similar to Render: connect the GitHub repo, Railway auto-detects Django,
set the same environment variables, and add a `Procfile`:

```
web: gunicorn Data.wsgi:application
```

## 4. Option C - PythonAnywhere (good for beginners, no gunicorn needed)

1. Upload the project (or `git clone` it in a Bash console).
2. Create a virtualenv and `pip install -r requirements.txt`.
3. Use the "Web" tab -> "Add a new web app" -> Manual configuration -> Django.
4. Point the WSGI file it gives you to `Data.wsgi.application`.
5. Set your project's static files mapping to `/static/` -> `.../staticfiles`.
6. Run `python manage.py migrate` from a Bash console there.

## 5. Option D - Your own VPS (DigitalOcean/AWS/etc.)

1. `gunicorn Data.wsgi:application --bind 0.0.0.0:8000`
2. Put nginx in front of it as a reverse proxy + to serve `/static/` and `/media/` directly.
3. Use `systemd` (or `supervisor`) to keep gunicorn running and restart it on crash/reboot.
4. Get a free TLS certificate with `certbot` (Let's Encrypt) so the site is HTTPS.

## 6. Media files (patient photos, lab reports)

Whatever platform you pick, `MEDIA_ROOT` needs persistent storage - on
Render/Railway's free tiers the filesystem resets on redeploy, so for real
use switch `DEFAULT_FILE_STORAGE` to an S3-compatible bucket
(`django-storages` + `boto3`) rather than local disk.

## 7. Automatic database backups

A management command handles this: `python manage.py auto_backup` copies
the SQLite database into `backups/` with a timestamp, and prunes old
copies (keeps the 14 most recent by default - override with `--keep N`).

Running it manually isn't "automatic" though - schedule it:

**Linux/macOS (cron):**
```bash
crontab -e
# add a line to run it every night at 2am:
0 2 * * * cd /path/to/hospital && /path/to/venv/bin/python manage.py auto_backup
```

**Windows (Task Scheduler):**
Create a Basic Task that runs daily, with:
- Program: `C:\path\to\venv\Scripts\python.exe`
- Arguments: `manage.py auto_backup`
- Start in: `C:\path\to\hospital`

**If you deploy to Render/Railway:** use their built-in Cron Job feature
(both support scheduled jobs) pointing at the same command, instead of a
traditional crontab.

Note this only backs up the SQLite file itself - if you switch to
Postgres/MySQL in production, use that database's native backup tool
(`pg_dump`/`mysqldump`) on the same schedule instead.

## 8. Payment gateway (if you enable real payments)

The bundled "Pay Now" flow (`/bills/<id>/pay/`) is a **simulated** demo -
it just marks a bill paid with no real money moving. To accept real
payments:

1. Sign up with a gateway (Razorpay, Stripe, PayU, etc.) and get API keys.
2. Store the keys in environment variables, never in code.
3. Replace `pay_bill()` in `Hospital/views.py` with the gateway's checkout
   flow, and only mark a bill `Paid` after verifying the gateway's
   signature/webhook - never on the client's word alone.
