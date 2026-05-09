from django.contrib import admin

from .models import Account, AccountField, AccountFieldValue, Opportunity, OpportunityLineItem, Product


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


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "updated_at")
    list_editable = ("active",)
    list_filter = ("active",)
    search_fields = ("name", "description")


class OpportunityLineItemInline(admin.TabularInline):
    extra = 1
    model = OpportunityLineItem


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    inlines = (OpportunityLineItemInline,)
    list_display = ("name", "account", "stage", "close_date", "updated_at")
    list_filter = ("stage", "close_date")
    search_fields = ("name", "account__first_name", "account__last_name", "description")


@admin.register(OpportunityLineItem)
class OpportunityLineItemAdmin(admin.ModelAdmin):
    list_display = ("opportunity", "product", "description", "updated_at")
    list_filter = ("product",)
    search_fields = ("opportunity__name", "product__name", "description")
