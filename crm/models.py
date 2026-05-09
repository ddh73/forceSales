from django.db import models
from django.urls import reverse


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
