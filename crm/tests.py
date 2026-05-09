from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse


class DashboardAccessTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_standard_user_can_view_dashboard(self):
        standard_group = Group.objects.get(name="Standard User")
        user = User.objects.create_user(username="standard", password="complex-pass-123")
        user.groups.add(standard_group)

        self.client.login(username="standard", password="complex-pass-123")
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Standard user")

    def test_superuser_sees_admin_panel_link(self):
        User.objects.create_superuser(username="admin", password="complex-pass-123")

        self.client.login(username="admin", password="complex-pass-123")
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Open admin")


class BrandingTests(TestCase):
    @override_settings(
        SITE_BRANDING={
            "name": "Acme Pipeline",
            "main_color": "#111111",
            "secondary_color": "#222222",
            "third_color": "#333333",
        }
    )
    def test_login_page_uses_configured_branding(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acme Pipeline")
        self.assertNotContains(response, "brand-mark")
        self.assertContains(response, "--primary: #111111")
        self.assertContains(response, "--secondary: #222222")
        self.assertContains(response, "--accent: #333333")
        self.assertNotContains(response, "Manage customers")
        self.assertContains(response, "Log in")
