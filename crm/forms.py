from django import forms

from .models import Account, AccountField, AccountFieldValue, Opportunity, OpportunityLineItem, Product


class AccountForm(forms.ModelForm):
    custom_field_prefix = "custom_field_"

    class Meta:
        model = Account
        fields = [
            "first_name",
            "last_name",
            "middle_name",
            "tax_id_code",
            "tax_id_number",
            "date_of_birth",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.account_fields = list(kwargs.pop("account_fields", AccountField.objects.filter(active=True)))
        super().__init__(*args, **kwargs)
        custom_values = self._custom_initial_values()

        for account_field in self.account_fields:
            field_name = self.custom_field_name(account_field)
            form_field = self._build_custom_form_field(account_field)
            form_field.initial = custom_values.get(account_field.pk, "")
            self.fields[field_name] = form_field

    def save(self, commit=True):
        account = super().save(commit=commit)
        if commit:
            self.save_custom_fields(account)
        return account

    def save_custom_fields(self, account):
        for account_field in self.account_fields:
            value = self.cleaned_data.get(self.custom_field_name(account_field), "")
            if value is None:
                value = ""
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            AccountFieldValue.objects.update_or_create(
                account=account,
                field=account_field,
                defaults={"value": str(value)},
            )

    def _custom_initial_values(self):
        if not self.instance or not self.instance.pk:
            return {}
        return {
            field_value.field_id: field_value.value
            for field_value in self.instance.custom_values.select_related("field").all()
        }

    def _build_custom_form_field(self, account_field):
        common_kwargs = {
            "label": account_field.label,
            "help_text": account_field.help_text,
            "required": account_field.required,
        }
        if account_field.field_type == AccountField.DATE:
            return forms.DateField(
                **common_kwargs,
                input_formats=["%Y-%m-%d"],
                widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            )
        if account_field.field_type == AccountField.NUMBER:
            return forms.DecimalField(**common_kwargs)
        if account_field.field_type == AccountField.EMAIL:
            return forms.EmailField(**common_kwargs)
        if account_field.field_type == AccountField.PHONE:
            return forms.CharField(**common_kwargs, widget=forms.TextInput(attrs={"type": "tel"}))
        return forms.CharField(**common_kwargs)

    def custom_field_name(self, account_field):
        return f"{self.custom_field_prefix}{account_field.pk}"


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "product_code", "description", "list_price", "active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_product_code(self):
        return self.cleaned_data.get("product_code") or None


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ["name", "account", "stage", "close_date", "description"]
        widgets = {
            "close_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class OpportunityLineItemForm(forms.ModelForm):
    class Meta:
        model = OpportunityLineItem
        fields = ["product", "quantity", "sales_price", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(active=True).order_by("name")
        self.fields["product"].help_text = "Choose the product this line item starts from."
        self.fields["sales_price"].help_text = "Defaults to the product list price when left blank."
        self.fields["sales_price"].required = False

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        sales_price = cleaned_data.get("sales_price")
        if product and sales_price is None:
            cleaned_data["sales_price"] = product.list_price
        return cleaned_data


OpportunityLineItemFormSet = forms.inlineformset_factory(
    Opportunity,
    OpportunityLineItem,
    form=OpportunityLineItemForm,
    extra=1,
    can_delete=True,
)
