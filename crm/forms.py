from django import forms

from .models import Account


class AccountForm(forms.ModelForm):
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
