from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Period, TimeSlot


class TimeSlotForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['name', 'start_time', 'end_time', 'order', 'is_break']


class PeriodForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Period
        fields = ['day', 'slot', 'class_subject']

    def __init__(self, *args, school_class=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school_class = school_class
        self.fields['slot'].queryset = TimeSlot.objects.filter(is_break=False)
        if school_class is not None:
            self.fields['class_subject'].queryset = school_class.class_subjects.select_related('subject', 'teacher__user')
            self.fields['class_subject'].label = 'Subject'

    def clean(self):
        cleaned = super().clean()
        self.instance.school_class = self.school_class
        return cleaned
