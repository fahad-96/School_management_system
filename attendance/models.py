from django.conf import settings
from django.db import models

from academics.models import Student


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'P', 'Present'
        ABSENT = 'A', 'Absent'
        LATE = 'L', 'Late'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PRESENT)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student']
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student} {self.date} {self.status}'
