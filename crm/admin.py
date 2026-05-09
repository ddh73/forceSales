from django.contrib import admin

from .models import Account, AccountField, AccountFieldValue


class AccountFieldValueInline(admin.TabularInline):
    extra = 0
    model = AccountFieldValue


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
    inlines = (AccountFieldValueInline,)
    list_display = ("full_name", "tax_id_code", "tax_id_number", "date_of_birth", "updated_at")
    list_filter = ("tax_id_code",)
    ordering = ("last_name", "first_name", "middle_name")
    search_fields = ("first_name", "middle_name", "last_name", "tax_id_code", "tax_id_number")


@admin.register(AccountField)
class AccountFieldAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Field setup",
            {
                "description": "Create and manage custom fields that normal users complete on account records.",
                "fields": ("label", "api_name", "field_type", "help_text", "required", "active", "display_order"),
            },
        ),
    )
    list_display = ("label", "api_name", "field_type", "required", "active", "display_order", "updated_at")
    list_editable = ("required", "active", "display_order")
    list_filter = ("field_type", "required", "active")
    ordering = ("display_order", "label")
    prepopulated_fields = {"api_name": ("label",)}
    search_fields = ("label", "api_name")
