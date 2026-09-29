from django import forms

from accounts.forms import BootstrapFormMixin
from academics.models import Student

from .models import FeeStructure, Payment


class FeeStructureForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['school_class', 'category', 'description', 'amount', 'due_date']


class PaymentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'fee_structure', 'amount', 'paid_on', 'method', 'reference', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.select_related('user', 'school_class')
        student = self.initial.get('student') or self.data.get('student')
        if student:
            self.fields['fee_structure'].queryset = FeeStructure.objects.filter(school_class__students=student)
