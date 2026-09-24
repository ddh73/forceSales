#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

python manage.py migrate --noinput
python manage.py bootstrap_admin
python manage.py collectstatic --noinput
exec gunicorn force_sales.wsgi:application --bind="0.0.0.0:${PORT:-8000}" --timeout 600 --access-logfile - --error-logfile -
