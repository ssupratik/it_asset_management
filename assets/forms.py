# assets/forms.py

from django import forms

from .models import Asset, Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["full_name", "designation", "email"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input"}),
            "designation": forms.TextInput(attrs={"class": "input"}),
            "email": forms.TextInput(attrs={"class": "input"}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = "__all__"
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "warranty_expiry": forms.DateInput(attrs={"type": "date"}),
        }
