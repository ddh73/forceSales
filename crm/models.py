from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Account(models.Model):
    """A customer account record tracked in the CRM."""

    SSN = "SSN"
    EIN = "EIN"

    TAX_ID_CODE_CHOICES = [
        (SSN, "SSN"),
        (EIN, "EIN"),
    ]

    first_name = models.CharField(blank=True, max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(blank=True, max_length=100)
    tax_id_code = models.CharField("Tax ID code", blank=True, choices=TAX_ID_CODE_CHOICES, max_length=32)
    tax_id_number = models.CharField("Tax ID number", blank=True, max_length=64)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name", "middle_name"]

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse("account_detail", kwargs={"pk": self.pk})

    @property
    def full_name(self):
        return " ".join(part for part in [self.first_name, self.middle_name, self.last_name] if part)


class Product(models.Model):
    """Sellable catalog item used to start opportunity line items."""

    name = models.CharField(max_length=150)
    product_code = models.CharField(blank=True, max_length=64, null=True, unique=True)
    description = models.TextField(blank=True)
    list_price = models.DecimalField(decimal_places=2, default=0, max_digits=12)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        if self.product_code:
            return f"{self.name} ({self.product_code})"
        return self.name

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})


class Opportunity(models.Model):
    """Sales deal with Salesforce-style stages and product-backed line items."""

    IN_PROGRESS = "in_progress"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

    STAGE_CHOICES = [
        (IN_PROGRESS, "In progress"),
        (CLOSED_WON, "Closed Won"),
        (CLOSED_LOST, "Closed Lost"),
    ]

    name = models.CharField(max_length=150)
    account = models.ForeignKey(Account, blank=True, null=True, on_delete=models.SET_NULL, related_name="opportunities")
    stage = models.CharField(choices=STAGE_CHOICES, default=IN_PROGRESS, max_length=32)
    close_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("opportunity_detail", kwargs={"pk": self.pk})

    @property
    def amount(self):
        return sum((line_item.total_price for line_item in self.line_items.all()), start=0)


class OpportunityLineItem(models.Model):
    """A quantity and sales price for one product on an opportunity."""

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="line_items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="opportunity_line_items")
    quantity = models.DecimalField(decimal_places=2, default=1, max_digits=10)
    sales_price = models.DecimalField("sales price", decimal_places=2, max_digits=12)
    description = models.CharField(blank=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product__name", "id"]

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    def clean(self):
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.sales_price is not None and self.sales_price < 0:
            raise ValidationError({"sales_price": "Sales price cannot be negative."})

    @property
    def total_price(self):
        return self.quantity * self.sales_price


class AccountField(models.Model):
    """Admin-managed custom field metadata for account records."""

    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"

    FIELD_TYPE_CHOICES = [
        (TEXT, "Text"),
        (NUMBER, "Number"),
        (DATE, "Date"),
        (EMAIL, "Email"),
        (PHONE, "Phone"),
    ]

    label = models.CharField(max_length=100)
    api_name = models.SlugField(
        "API name",
        blank=True,
        help_text="Stable internal name. Leave blank to generate one from the label.",
        max_length=100,
        unique=True,
    )
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default=TEXT)
    help_text = models.CharField(blank=True, max_length=255)
    required = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "label"]

    def __str__(self):
        return self.label

    def clean(self):
        if not self.api_name:
            self.api_name = slugify(self.label).replace("-", "_")
        if self.api_name:
            self.api_name = self.api_name.replace("-", "_")
        if self.api_name in {"first_name", "last_name", "middle_name", "tax_id_code", "tax_id_number", "date_of_birth"}:
            raise ValidationError({"api_name": "Choose an API name that does not match a standard account field."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AccountFieldValue(models.Model):
    """Stores the value for an admin-managed custom account field."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="custom_values")
    field = models.ForeignKey(AccountField, on_delete=models.CASCADE, related_name="values")
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["field__display_order", "field__label"]
        unique_together = ("account", "field")

    def __str__(self):
        return f"{self.account} - {self.field}"
