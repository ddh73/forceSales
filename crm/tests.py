from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Account, AccountField, AccountFieldValue


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
        cls.custom_field = AccountField.objects.create(
            label="Preferred Branch",
            field_type=AccountField.TEXT,
            help_text="Branch assigned to this account.",
            display_order=1,
        )
        AccountFieldValue.objects.create(account=cls.account, field=cls.custom_field, value="London")

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

    def test_account_list_displays_current_accounts_and_create_action(self):
        self.client.login(username="standard", password="complex-pass-123")

        response = self.client.get(reverse("account_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada M Lovelace")
        self.assertContains(response, self.account.get_absolute_url())
        self.assertContains(response, reverse("account_create"))
        self.assertContains(response, "New account")

    def test_standard_user_can_create_account_with_admin_defined_fields(self):
        self.client.login(username="standard", password="complex-pass-123")
        response = self.client.get(reverse("account_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preferred Branch")
        self.assertContains(response, "Branch assigned to this account.")

        create_response = self.client.post(
            reverse("account_create"),
            {
                "first_name": "Grace",
                "middle_name": "B",
                "last_name": "Hopper",
                "tax_id_code": "SSN",
                "tax_id_number": "111-22-3333",
                "date_of_birth": "1906-12-09",
                f"custom_field_{self.custom_field.pk}": "Arlington",
            },
        )

        account = Account.objects.get(first_name="Grace")
        self.assertRedirects(create_response, account.get_absolute_url())
        self.assertEqual(
            AccountFieldValue.objects.get(account=account, field=self.custom_field).value,
            "Arlington",
        )


    def test_only_last_name_is_required_to_create_account(self):
        self.client.login(username="standard", password="complex-pass-123")

        response = self.client.post(
            reverse("account_create"),
            {
                "first_name": "",
                "middle_name": "",
                "last_name": "Solo",
                "tax_id_code": "",
                "tax_id_number": "",
                "date_of_birth": "",
                f"custom_field_{self.custom_field.pk}": "",
            },
        )

        account = Account.objects.get(last_name="Solo")
        self.assertRedirects(response, account.get_absolute_url())
        self.assertEqual(account.first_name, "")
        self.assertEqual(account.tax_id_code, "")
        self.assertIsNone(account.date_of_birth)

    def test_tax_id_code_is_ssn_or_ein_picklist(self):
        self.client.login(username="standard", password="complex-pass-123")

        response = self.client.get(reverse("account_create"))

        self.assertContains(response, '<option value="SSN">SSN</option>', html=True)
        self.assertContains(response, '<option value="EIN">EIN</option>', html=True)

        invalid_response = self.client.post(
            reverse("account_create"),
            {
                "first_name": "",
                "middle_name": "",
                "last_name": "Invalid Picklist",
                "tax_id_code": "TIN",
                "tax_id_number": "",
                "date_of_birth": "",
                f"custom_field_{self.custom_field.pk}": "",
            },
        )

        self.assertEqual(invalid_response.status_code, 200)
        self.assertFalse(Account.objects.filter(last_name="Invalid Picklist").exists())
        self.assertContains(invalid_response, "Select a valid choice")

    def test_account_detail_starts_read_only_and_can_update_fields(self):
        self.client.login(username="standard", password="complex-pass-123")
        response = self.client.get(self.account.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Fields start read-only")
        self.assertContains(response, 'field.setAttribute("readonly", "readonly")')
        self.assertContains(response, '<button class="save-button is-hidden" type="submit">Save changes</button>', html=True)
        self.assertContains(response, 'saveButton.classList.remove("is-hidden")')
        self.assertContains(response, "123-45-6789")
        self.assertContains(response, "Preferred Branch")
        self.assertContains(response, "London")

        update_response = self.client.post(
            self.account.get_absolute_url(),
            {
                "first_name": "Augusta Ada",
                "middle_name": "M",
                "last_name": "Lovelace",
                "tax_id_code": "SSN",
                "tax_id_number": "987-65-4321",
                "date_of_birth": "1815-12-10",
                f"custom_field_{self.custom_field.pk}": "Oxford",
            },
        )

        self.assertRedirects(update_response, self.account.get_absolute_url())
        self.account.refresh_from_db()
        self.assertEqual(self.account.first_name, "Augusta Ada")
        self.assertEqual(self.account.tax_id_number, "987-65-4321")
        self.assertEqual(
            AccountFieldValue.objects.get(account=self.account, field=self.custom_field).value,
            "Oxford",
        )


class AccountAdminTests(TestCase):
    def test_staff_can_add_and_change_accounts_in_admin(self):
        User.objects.create_superuser(username="admin", password="complex-pass-123")
        self.client.login(username="admin", password="complex-pass-123")
        account = Account.objects.create(
            first_name="Katherine",
            middle_name="",
            last_name="Johnson",
            tax_id_code="SSN",
            tax_id_number="222-33-4444",
            date_of_birth=date(1918, 8, 26),
        )

        add_response = self.client.get(reverse("admin:crm_account_add"))
        change_response = self.client.get(reverse("admin:crm_account_change", args=[account.pk]))

        self.assertEqual(add_response.status_code, 200)
        self.assertEqual(change_response.status_code, 200)
        self.assertContains(add_response, "Tax ID code")
        self.assertContains(add_response, '<option value="SSN">SSN</option>', html=True)
        self.assertContains(add_response, '<option value="EIN">EIN</option>', html=True)
        self.assertContains(add_response, "Date of birth")
        self.assertContains(change_response, 'name="_save"')

    def test_staff_can_manage_account_field_definitions_in_admin(self):
        User.objects.create_superuser(username="admin", password="complex-pass-123")
        self.client.login(username="admin", password="complex-pass-123")

        response = self.client.get(reverse("admin:crm_accountfield_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create and manage custom fields")
        self.assertContains(response, "Field type")


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
