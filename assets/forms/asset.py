from django import forms

from ..models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name",
            "asset_type",
            "serial_number",
            "purchase_date",
            "warranty_expiry",
            "assigned_to",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "warranty_expiry": forms.DateInput(
                attrs={"type": "date", "class": "input"}
            ),
            "assigned_to": forms.Select(attrs={"class": "select"}),
            "name": forms.TextInput(attrs={"class": "input"}),
            "asset_type": forms.Select(attrs={"class": "select"}),
            "serial_number": forms.TextInput(attrs={"class": "input"}),
        }
