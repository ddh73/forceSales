# Force Sales

Force Sales is a Django starter CRM intended to grow into a Salesforce-style web app. The first version is intentionally small: every application page is login restricted, and authenticated users can be separated into an admin role or a standard-user role.

## What is included

- Django project configured for local development and Azure App Service deployment.
- Login/logout using Django's built-in authentication views.
- A protected dashboard at `/dashboard/`.
- Default `CRM Admin` and `Standard User` Django groups created by the first migration.
- Static-file serving with WhiteNoise for Azure.
- `startup.sh` and `Procfile` for App Service startup.
- Environment-variable based settings for secret key, allowed hosts, CSRF trusted origins, SSL redirect, database connection, and site branding.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and log in with the superuser account. Local development defaults `DJANGO_DEBUG` to `True` so Django serves the stylesheet while using `runserver`; keep `DJANGO_DEBUG=False` in Azure.

## Branding and theme colors

The default site name and theme colors live in `force_sales/site_branding.py`, which works like a small style configuration file:

```python
WEBSITE_NAME = "Force Sales"
MAIN_STYLE_COLOR = "#0b5cab"
SECONDARY_STYLE_COLOR = "#35a1ff"
THIRD_STYLE_COLOR = "#20c997"
```

The templates read those values and convert them into CSS custom properties used by `static/css/site.css`. In Azure, you can override the same values without changing code by setting these application settings:

```text
WEBSITE_NAME=Your CRM Name
MAIN_STYLE_COLOR=#0b5cab
SECONDARY_STYLE_COLOR=#35a1ff
THIRD_STYLE_COLOR=#20c997
```

Use six-digit hex colors so the theme can be safely rendered into the page.

## Roles and users

The migration `crm/migrations/0001_create_default_groups.py` creates two groups:

- `CRM Admin` - intended for users who can administer CRM users and data.
- `Standard User` - intended for normal authenticated users.

To create a standard user:

1. Log in to `/admin/` with a superuser account.
2. Create a user in **Authentication and Authorization > Users**.
3. Add that user to the `Standard User` group.
4. Leave **Staff status** unchecked unless the user needs Django admin access.

To create an app admin:

1. Create or edit a user in `/admin/`.
2. Add the user to the `CRM Admin` group.
3. Enable **Staff status** if the user should access the Django admin site.

## Deploy to Azure App Service

These steps assume an Azure App Service for Linux running Python and, for production, an Azure PostgreSQL database.

1. Create the App Service and connect your repository as the deployment source.
2. Configure the startup command to:

   ```bash
   bash startup.sh
   ```

3. Add App Service application settings:

   ```text
   DJANGO_SECRET_KEY=<long random secret>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=<your-app-name>.azurewebsites.net
   DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-app-name>.azurewebsites.net
   DJANGO_SECURE_SSL_REDIRECT=True
   WEBSITE_NAME=<your CRM name>
   MAIN_STYLE_COLOR=#0b5cab
   SECONDARY_STYLE_COLOR=#35a1ff
   THIRD_STYLE_COLOR=#20c997
   DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
   ```

4. Set `SCM_DO_BUILD_DURING_DEPLOYMENT=true` so Azure installs the Python dependencies. Keep the startup command set to `bash startup.sh`; launching Gunicorn directly skips database initialization.
5. Deploy the app. `startup.sh` runs migrations, optionally creates the initial admin, collects static files, and starts Gunicorn. GitHub Actions checks migrations, tests the app, and exercises startup/login/restart before deployment. The deployment ZIP contains only tracked files.
6. To provision the first admin automatically, set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, and optionally `DJANGO_SUPERUSER_EMAIL` in Azure application settings. There are no built-in credentials. Startup leaves an existing user and password unchanged; remove the bootstrap settings after the first successful login. Alternatively use an App Service SSH session:

   ```bash
   python manage.py createsuperuser
   ```

### SQLite on the current single-instance App Service

When `DATABASE_URL` is unset, Azure uses `/home/site/data/db.sqlite3`, outside the temporary Oryx app directory. Locally it uses `db.sqlite3` beside `manage.py`. `DJANGO_SQLITE_PATH` overrides that fallback; `DATABASE_URL` always takes precedence. Keep SQLite on a single instance and back it up; use PostgreSQL before scaling to multiple instances.

If an older deployment has real data in its app-directory SQLite file, back up that database while the old instance is still running and restore it to the persistent path **before** switching deployment/configuration. Do not copy a live SQLite file with ordinary filesystem copying or overwrite an existing persistent database. The app intentionally does not guess which old database to import.

Azure defaults to `DJANGO_DEBUG=False` and secure cookies. Set a unique `DJANGO_SECRET_KEY` in application settings; the fallback key is for local development only. Static files use Django 5.2's `STORAGES` configuration and WhiteNoise manifest storage.

## Useful commands

```bash
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```
