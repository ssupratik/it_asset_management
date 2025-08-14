from django import forms

from ..models import Asset, Employee, History


class HistoryForm(forms.ModelForm):
    class Meta:
        model = History
        fields = ["asset", "from_employee", "to_employee", "transfer_date", "remarks"]
        widgets = {
            "transfer_date": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "remarks": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["asset"].queryset = Asset.objects.all()
        self.fields["from_employee"].queryset = Employee.objects.all()
        self.fields["to_employee"].queryset = Employee.objects.all()
