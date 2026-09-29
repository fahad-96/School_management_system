from django.core.exceptions import ValidationError
from django.db import models

from academics.models import SchoolClass, Student, Subject

GRADE_BANDS = [(90, 'A+'), (80, 'A'), (70, 'B+'), (60, 'B'), (50, 'C'), (40, 'D')]


def grade_for(percentage):
    for cutoff, grade in GRADE_BANDS:
        if percentage >= cutoff:
            return grade
    return 'F'


class Exam(models.Model):
    name = models.CharField(max_length=100, help_text='e.g. Mid Term')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='exams')
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False, help_text='Students/parents can see results once published')

    class Meta:
        ordering = ['-start_date', 'name']
        unique_together = ('name', 'school_class')

    def __str__(self):
        return f'{self.name} · {self.school_class}'

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date must be on or after the start date.'})


class ExamSubject(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=6, decimal_places=2, default=33)
    exam_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['exam_date', 'subject__name']
        unique_together = ('exam', 'subject')

    def __str__(self):
        return f'{self.exam} · {self.subject}'


class Mark(models.Model):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    score = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('exam_subject', 'student')

    def __str__(self):
        return f'{self.student} · {self.exam_subject}: {self.score}'

    def clean(self):
        if self.score is not None and self.exam_subject_id:
            if self.score < 0 or self.score > self.exam_subject.max_marks:
                raise ValidationError({'score': f'Score must be between 0 and {self.exam_subject.max_marks}.'})

    @property
    def percentage(self):
        return round(float(self.score) * 100 / float(self.exam_subject.max_marks), 1)

    @property
    def grade(self):
        return grade_for(self.percentage)

    @property
    def passed(self):
        return self.score >= self.exam_subject.pass_marks
