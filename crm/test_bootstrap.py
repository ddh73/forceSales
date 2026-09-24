import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class BootstrapAdminTests(TestCase):
    def run_bootstrap(self, **env):
        output = StringIO()
        with patch.dict(os.environ, env, clear=True):
            call_command("bootstrap_admin", stdout=output)
        return output.getvalue()

    def test_no_configuration_creates_no_user(self):
        self.run_bootstrap()
        self.assertFalse(get_user_model().objects.exists())

    def test_creates_admin_and_supports_login(self):
        output = self.run_bootstrap(
            DJANGO_SUPERUSER_USERNAME="initial-admin",
            DJANGO_SUPERUSER_PASSWORD="test-only-password!",
        )
        user = get_user_model().objects.get(username="initial-admin")
        self.assertTrue(user.is_staff and user.is_superuser and user.is_active)
        self.assertTrue(self.client.login(username=user.username, password="test-only-password!"))
        self.assertNotIn("test-only-password!", output)

    def test_restart_does_not_reset_password_or_elevate_existing_user(self):
        user = get_user_model().objects.create_user("existing", password="original")
        self.run_bootstrap(DJANGO_SUPERUSER_USERNAME="existing", DJANGO_SUPERUSER_PASSWORD="different")
        user.refresh_from_db()
        self.assertTrue(user.check_password("original"))
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_existing_user_does_not_require_bootstrap_password(self):
        get_user_model().objects.create_superuser("existing", password="original")
        self.run_bootstrap(DJANGO_SUPERUSER_USERNAME="existing")

    def test_incomplete_configuration_fails_before_creating_user(self):
        for env in ({"DJANGO_SUPERUSER_USERNAME": "admin"}, {"DJANGO_SUPERUSER_PASSWORD": "test"}):
            with self.subTest(env=list(env)), self.assertRaises(CommandError):
                self.run_bootstrap(**env)
        self.assertFalse(get_user_model().objects.exists())
