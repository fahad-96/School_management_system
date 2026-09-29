from django import forms
from django.utils import timezone

from accounts.forms import BootstrapFormMixin
from academics.models import SchoolClass


class AttendanceSelectForm(BootstrapFormMixin, forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none(), label='Class')
    date = forms.DateField(initial=timezone.localdate)

    def __init__(self, *args, classes=None, **kwargs):
        super().__init__(*args, **kwargs)
        if classes is not None:
            self.fields['school_class'].queryset = classes


class MonthSelectForm(BootstrapFormMixin, forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.none(), label='Class')
    month = forms.CharField(widget=forms.TextInput(attrs={'type': 'month'}))

    def __init__(self, *args, classes=None, **kwargs):
        super().__init__(*args, **kwargs)
        if classes is not None:
            self.fields['school_class'].queryset = classes
