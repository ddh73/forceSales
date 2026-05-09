from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Account details",
            {
                "fields": (
                    "first_name",
                    "middle_name",
                    "last_name",
                    "tax_id_code",
                    "tax_id_number",
                    "date_of_birth",
                )
            },
        ),
    )
    list_display = ("full_name", "tax_id_code", "tax_id_number", "date_of_birth", "updated_at")
    list_filter = ("tax_id_code",)
    ordering = ("last_name", "first_name", "middle_name")
    search_fields = ("first_name", "middle_name", "last_name", "tax_id_code", "tax_id_number")
