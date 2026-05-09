from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Account(models.Model):
    """A customer account record tracked in the CRM."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(blank=True, max_length=100)
    tax_id_code = models.CharField("Tax ID code", max_length=32)
    tax_id_number = models.CharField("Tax ID number", max_length=64)
    date_of_birth = models.DateField()
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
