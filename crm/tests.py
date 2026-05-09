from datetime import date

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, reverse

from .models import (
    Account,
    AccountField,
    AccountFieldValue,
    Opportunity,
    OpportunityLineItem,
    Product,
    ProfileObjectPermission,
)


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
            owner=cls.user,
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
        self.assertContains(response, "Accounts")
        self.assertNotContains(response, "CRM")
        self.assertNotContains(response, "total")
        self.assertNotContains(response, "Create and edit records")
        self.assertNotContains(response, "Coming soon")

    def test_account_list_displays_current_accounts_and_create_action(self):
        self.client.login(username="standard", password="complex-pass-123")

        response = self.client.get(reverse("account_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ada M Lovelace")
        self.assertContains(response, self.account.get_absolute_url())
        self.assertContains(response, reverse("account_create"))
        self.assertContains(response, "New account")

    def test_standard_user_has_full_account_access_by_default(self):
        other_user = User.objects.create_user(username="other", password="complex-pass-123")
        other_account = Account.objects.create(owner=other_user, first_name="Shared", last_name="Account")

        self.client.login(username="standard", password="complex-pass-123")
        list_response = self.client.get(reverse("account_list"))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Ada M Lovelace")
        self.assertContains(list_response, "Shared Account")

        update_response = self.client.post(
            other_account.get_absolute_url(),
            {
                "first_name": "Shared",
                "middle_name": "",
                "last_name": "Edited",
                "tax_id_code": "",
                "tax_id_number": "",
                "date_of_birth": "",
                f"custom_field_{self.custom_field.pk}": "",
            },
        )

        self.assertRedirects(update_response, other_account.get_absolute_url())
        other_account.refresh_from_db()
        self.assertEqual(other_account.last_name, "Edited")

    def test_standard_user_has_owned_opportunity_access_by_default(self):
        other_user = User.objects.create_user(username="other", password="complex-pass-123")
        Opportunity.objects.create(owner=other_user, name="Hidden opportunity")

        self.client.login(username="standard", password="complex-pass-123")
        list_response = self.client.get(reverse("opportunity_list"))
        create_response = self.client.get(reverse("opportunity_create"))

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, "Hidden opportunity")
        self.assertEqual(create_response.status_code, 200)

    def test_admin_profile_has_default_access_for_every_crm_object(self):
        admin_group = Group.objects.get(name="CRM Admin")
        for model in [
            Account,
            AccountField,
            AccountFieldValue,
            Product,
            Opportunity,
            OpportunityLineItem,
            ProfileObjectPermission,
        ]:
            permission = ProfileObjectPermission.objects.get(
                profile=admin_group,
                content_type=ContentType.objects.get_for_model(model),
            )
            self.assertTrue(permission.can_read)
            self.assertTrue(permission.can_write)
            self.assertTrue(permission.can_read_all)
            self.assertTrue(permission.can_edit_all)

    def test_standard_profile_default_object_access(self):
        standard_group = Group.objects.get(name="Standard User")
        account_permission = ProfileObjectPermission.objects.get(
            profile=standard_group,
            content_type=ContentType.objects.get_for_model(Account),
        )
        opportunity_permission = ProfileObjectPermission.objects.get(
            profile=standard_group,
            content_type=ContentType.objects.get_for_model(Opportunity),
        )
        opportunity_line_item_permission = ProfileObjectPermission.objects.get(
            profile=standard_group,
            content_type=ContentType.objects.get_for_model(OpportunityLineItem),
        )
        product_permission = ProfileObjectPermission.objects.get(
            profile=standard_group,
            content_type=ContentType.objects.get_for_model(Product),
        )

        self.assertTrue(account_permission.can_read)
        self.assertTrue(account_permission.can_write)
        self.assertTrue(account_permission.can_read_all)
        self.assertTrue(account_permission.can_edit_all)
        self.assertTrue(opportunity_permission.can_read)
        self.assertTrue(opportunity_permission.can_write)
        self.assertFalse(opportunity_permission.can_read_all)
        self.assertFalse(opportunity_permission.can_edit_all)
        self.assertTrue(opportunity_line_item_permission.can_read)
        self.assertTrue(opportunity_line_item_permission.can_write)
        self.assertFalse(opportunity_line_item_permission.can_read_all)
        self.assertFalse(opportunity_line_item_permission.can_edit_all)
        self.assertTrue(product_permission.can_read)
        self.assertFalse(product_permission.can_write)
        self.assertFalse(product_permission.can_read_all)
        self.assertFalse(product_permission.can_edit_all)

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


class OpportunityViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="seller", password="complex-pass-123")
        cls.account = Account.objects.create(owner=cls.user, first_name="Dorothy", last_name="Vaughan")
        cls.product = Product.objects.create(name="Implementation Package", description="Implementation services")
        cls.opportunity = Opportunity.objects.create(
            owner=cls.user,
            name="Vaughan expansion",
            account=cls.account,
            stage=Opportunity.IN_PROGRESS,
        )
        OpportunityLineItem.objects.create(
            opportunity=cls.opportunity,
            product=cls.product,
            description="Initial product notes",
        )

    def test_opportunity_list_requires_login(self):
        response = self.client.get(reverse("opportunity_list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_dashboard_links_to_opportunities_without_product_management(self):
        self.client.login(username="seller", password="complex-pass-123")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("opportunity_list"))
        self.assertContains(response, "Opportunities")
        self.assertNotContains(response, "Track stages and product line items")
        self.assertNotContains(response, "Product catalog")
        self.assertNotContains(response, "total")
        with self.assertRaises(NoReverseMatch):
            reverse("product_list")

    def test_user_can_create_opportunity_with_stage_picklist(self):
        self.client.login(username="seller", password="complex-pass-123")

        response = self.client.get(reverse("opportunity_create"))
        self.assertContains(response, 'name="account_search"')
        self.assertContains(response, 'placeholder="Search accounts by name"')
        self.assertContains(response, 'data-account-search-url="/accounts/search/"')
        self.assertContains(response, 'type="hidden" name="account"')
        self.assertNotContains(response, '<select name="account"')
        self.assertContains(response, '<option value="in_progress" selected>In progress</option>', html=True)
        self.assertContains(response, '<option value="closed_won">Closed Won</option>', html=True)
        self.assertContains(response, '<option value="closed_lost">Closed Lost</option>', html=True)

        create_response = self.client.post(
            reverse("opportunity_create"),
            {
                "name": "New services deal",
                "account": self.account.pk,
                "stage": Opportunity.CLOSED_WON,
                "close_date": "2026-05-31",
                "description": "Services expansion",
            },
        )

        opportunity = Opportunity.objects.get(name="New services deal")
        self.assertRedirects(create_response, opportunity.get_absolute_url())
        self.assertEqual(opportunity.stage, Opportunity.CLOSED_WON)

    def test_account_search_requires_login_and_returns_matches(self):
        login_response = self.client.get(reverse("account_search"), {"q": "Dorothy"})
        self.assertEqual(login_response.status_code, 302)
        self.assertIn(reverse("login"), login_response["Location"])

        self.client.login(username="seller", password="complex-pass-123")
        response = self.client.get(reverse("account_search"), {"q": "Dorothy Vaughan"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": [{"id": self.account.pk, "label": "Dorothy Vaughan"}]})

    def test_typed_account_without_search_selection_is_invalid(self):
        self.client.login(username="seller", password="complex-pass-123")

        response = self.client.post(
            reverse("opportunity_create"),
            {
                "name": "Unmatched account deal",
                "account_search": "Dorothy Vaughan",
                "account": "",
                "stage": Opportunity.IN_PROGRESS,
                "close_date": "",
                "description": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select an account from the search results.")
        self.assertFalse(Opportunity.objects.filter(name="Unmatched account deal").exists())

    def test_opportunity_detail_manages_product_backed_line_items(self):
        self.client.login(username="seller", password="complex-pass-123")
        response = self.client.get(self.opportunity.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Opportunity line items")
        self.assertContains(response, "Product name")
        self.assertContains(response, "Description")
        self.assertContains(response, "Implementation Package")
        self.assertContains(response, 'name="account_search"')
        self.assertContains(response, 'value="Dorothy Vaughan"')
        self.assertContains(response, f'type="hidden" name="account" value="{self.account.pk}"')
        self.assertNotContains(response, '<select name="account"')
        self.assertNotContains(response, "Quantity")
        self.assertNotContains(response, "Sales price")
        self.assertNotContains(response, "$5000.00")
        self.assertNotContains(response, "Manage products")
        self.assertNotContains(response, "Create a product first")
        self.assertNotContains(response, "Add the product name and an optional description")
        self.assertNotContains(response, "Choose the product for this opportunity.")
        self.assertNotContains(response, "Optional notes for this opportunity product.")

        update_response = self.client.post(
            self.opportunity.get_absolute_url(),
            {
                "name": "Vaughan expansion updated",
                "account": self.account.pk,
                "stage": Opportunity.CLOSED_LOST,
                "close_date": "",
                "description": "",
                "line_items-TOTAL_FORMS": "2",
                "line_items-INITIAL_FORMS": "1",
                "line_items-MIN_NUM_FORMS": "0",
                "line_items-MAX_NUM_FORMS": "1000",
                "line_items-0-id": self.opportunity.line_items.first().pk,
                "line_items-0-opportunity": self.opportunity.pk,
                "line_items-0-product": self.product.pk,
                "line_items-0-description": "Customer-facing product notes",
                "line_items-1-id": "",
                "line_items-1-opportunity": self.opportunity.pk,
                "line_items-1-product": "",
                "line_items-1-description": "",
            },
        )

        self.assertRedirects(update_response, self.opportunity.get_absolute_url())
        self.opportunity.refresh_from_db()
        line_item = self.opportunity.line_items.get()
        self.assertEqual(self.opportunity.stage, Opportunity.CLOSED_LOST)
        self.assertEqual(line_item.product, self.product)
        self.assertEqual(line_item.description, "Customer-facing product notes")


class ProfileObjectPermissionAdminTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username="admin-access", password="complex-pass-123")
        self.client.login(username="admin-access", password="complex-pass-123")

    def test_change_form_loads_access_lookup_script(self):
        standard_group = Group.objects.get(name="Standard User")
        permission = ProfileObjectPermission.objects.get(
            profile=standard_group,
            content_type=ContentType.objects.get_for_model(Account),
        )

        response = self.client.get(reverse("admin:crm_profileobjectpermission_change", args=[permission.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "crm/admin/profile_object_permission.js")

    def test_lookup_returns_existing_access_for_selected_profile_and_object(self):
        standard_group = Group.objects.get(name="Standard User")
        opportunity_permission = ProfileObjectPermission.objects.get(
            profile=standard_group,
            content_type=ContentType.objects.get_for_model(Opportunity),
        )

        response = self.client.get(
            reverse("admin:crm_profileobjectpermission_lookup"),
            {
                "profile": standard_group.pk,
                "content_type": ContentType.objects.get_for_model(Opportunity).pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "found": True,
                "id": opportunity_permission.pk,
                "change_url": reverse("admin:crm_profileobjectpermission_change", args=[opportunity_permission.pk]),
                "can_read": True,
                "can_write": True,
                "can_read_all": False,
                "can_edit_all": False,
            },
        )


class OpportunityAdminTests(TestCase):
    def test_opportunity_admin_uses_correct_plural_name(self):
        self.assertEqual(Opportunity._meta.verbose_name_plural, "opportunities")

    def test_staff_can_manage_opportunities_products_and_line_items(self):
        User.objects.create_superuser(username="admin2", password="complex-pass-123")
        self.client.login(username="admin2", password="complex-pass-123")
        product = Product.objects.create(name="Support Plan", description="Support services")
        opportunity = Opportunity.objects.create(name="Support renewal", stage=Opportunity.IN_PROGRESS)
        OpportunityLineItem.objects.create(
            opportunity=opportunity,
            product=product,
            description="Renewal support",
        )

        product_response = self.client.get(reverse("admin:crm_product_add"))
        opportunity_response = self.client.get(reverse("admin:crm_opportunity_change", args=[opportunity.pk]))

        self.assertEqual(product_response.status_code, 200)
        self.assertEqual(opportunity_response.status_code, 200)
        self.assertContains(product_response, "Description")
        self.assertNotContains(product_response, "List price")
        self.assertContains(opportunity_response, "Opportunity line items")
        self.assertContains(opportunity_response, "Closed Won")
