from django import forms

from ..models import Asset, AssetDocument

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "type",
            "make_model",
            "serial_number",
            "year_of_purchase",
            "ram",
            "hdd",
            "ssd",
            "os",
            "condition",
            "remarks",
            "alloted_to",
            "is_active",
        ]
        widgets = {
            "type": forms.Select(attrs={"class": "select"}),
            "make_model": forms.TextInput(attrs={"class": "input"}),
            "serial_number": forms.TextInput(attrs={"class": "input"}),
            "year_of_purchase": forms.NumberInput(attrs={"class": "input"}),
            "ram": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. 8GB"}),
            "hdd": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. 1TB"}),
            "ssd": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. 256GB"}),
            "os": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. Windows 10"}),
            "condition": forms.Select(attrs={"class": "select"}),
            "remarks": forms.Textarea(attrs={"class": "textarea"}),
            "alloted_to": forms.Select(attrs={"class": "select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }

class AssetDocumentForm(forms.ModelForm):
    class Meta:
        model = AssetDocument
        fields = ['name', 'document']