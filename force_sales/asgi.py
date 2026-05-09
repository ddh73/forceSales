"""ASGI config for the Force Sales starter CRM project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "force_sales.settings")

application = get_asgi_application()
