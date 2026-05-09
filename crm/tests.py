from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Account


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


class AccountViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="standard", password="complex-pass-123")
        cls.account = Account.objects.create(
            first_name="Ada",
            middle_name="M",
            last_name="Lovelace",
            tax_id_code="SSN",
            tax_id_number="123-45-6789",
            date_of_birth=date(1815, 12, 10),
        )

    def test_account_list_requires_login(self):
        response = self.client.get(reverse("account_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_dashboard_links_to_account_tab(self):
        self.client.login(username="standard", password="complex-pass-123")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("account_list"))
        self.assertContains(response, "1 total")

    def test_account_list_displays_current_accounts(self):
        self.client.login(username="standard", password="complex-pass-123")

        response = self.client.get(reverse("account_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada M Lovelace")
        self.assertContains(response, self.account.get_absolute_url())

    def test_account_detail_starts_read_only_and_can_update_fields(self):
        self.client.login(username="standard", password="complex-pass-123")
        response = self.client.get(self.account.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fields start read-only")
        self.assertContains(response, 'field.setAttribute("readonly", "readonly")')
        self.assertContains(response, "123-45-6789")

        update_response = self.client.post(
            self.account.get_absolute_url(),
            {
                "first_name": "Augusta Ada",
                "middle_name": "M",
                "last_name": "Lovelace",
                "tax_id_code": "SSN",
                "tax_id_number": "987-65-4321",
                "date_of_birth": "1815-12-10",
            },
        )

        self.assertRedirects(update_response, self.account.get_absolute_url())
        self.account.refresh_from_db()
        self.assertEqual(self.account.first_name, "Augusta Ada")
        self.assertEqual(self.account.tax_id_number, "987-65-4321")


class AccountAdminTests(TestCase):
    def test_staff_can_open_account_add_page_in_admin(self):
        User.objects.create_superuser(username="admin", password="complex-pass-123")
        self.client.login(username="admin", password="complex-pass-123")

        response = self.client.get(reverse("admin:crm_account_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tax ID code")
        self.assertContains(response, "Date of birth")


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
