"""Create an explicitly configured initial admin without resetting existing users."""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create an initial admin from DJANGO_SUPERUSER_* environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not username and not password:
            self.stdout.write("Admin bootstrap not configured; skipping.")
            return
        if not username:
            raise CommandError("DJANGO_SUPERUSER_USERNAME is required for admin bootstrap.")
        User = get_user_model()
        with transaction.atomic():
            if User.objects.filter(username=username).exists():
                self.stdout.write("Admin bootstrap: existing user left unchanged.")
                return
            if not password:
                raise CommandError("DJANGO_SUPERUSER_PASSWORD is required to create the initial admin.")
            User.objects.create_superuser(
                username=username,
                password=password,
                email=os.environ.get("DJANGO_SUPERUSER_EMAIL", ""),
            )
        self.stdout.write(self.style.SUCCESS("Initial admin created."))
