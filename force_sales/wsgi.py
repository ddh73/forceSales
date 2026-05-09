"""WSGI config for the Force Sales starter CRM project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "force_sales.settings")

application = get_wsgi_application()
