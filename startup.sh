#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn force_sales.wsgi:application --bind=0.0.0.0:${PORT:-8000}
