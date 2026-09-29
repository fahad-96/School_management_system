from django import forms

from accounts.forms import BootstrapFormMixin
from academics.models import Subject

from .models import Exam, ExamSubject


class ExamForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'school_class', 'start_date', 'end_date', 'is_published']


class ExamSubjectForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ExamSubject
        fields = ['subject', 'max_marks', 'pass_marks', 'exam_date']

    def __init__(self, *args, exam=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam = exam
        if exam is not None:
            taken = exam.subjects.values_list('subject_id', flat=True)
            class_subjects = exam.school_class.class_subjects.values_list('subject_id', flat=True)
            self.fields['subject'].queryset = Subject.objects.filter(pk__in=class_subjects).exclude(pk__in=taken)

    def save(self, commit=True):
        self.instance.exam = self.exam
        return super().save(commit=commit)
