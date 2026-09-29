from django.core.exceptions import ValidationError
from django.db import models

from academics.models import ClassSubject, SchoolClass

DAYS = [(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday')]


class TimeSlot(models.Model):
    name = models.CharField(max_length=30, help_text='e.g. Period 1')
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveIntegerField(unique=True)
    is_break = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.name} ({self.start_time:%H:%M}–{self.end_time:%H:%M})'

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})


class Period(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='periods')
    day = models.IntegerField(choices=DAYS)
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='periods')
    class_subject = models.ForeignKey(ClassSubject, on_delete=models.CASCADE, related_name='periods')

    class Meta:
        ordering = ['day', 'slot__order']
        unique_together = ('school_class', 'day', 'slot')

    def __str__(self):
        return f'{self.school_class} {self.get_day_display()} {self.slot.name}: {self.class_subject.subject}'

    @property
    def teacher(self):
        return self.class_subject.teacher

    def clean(self):
        if self.class_subject_id and self.school_class_id and self.class_subject.school_class_id != self.school_class_id:
            raise ValidationError({'class_subject': 'That subject is not assigned to this class.'})
        if self.slot_id and self.slot.is_break:
            raise ValidationError({'slot': 'Cannot schedule a lesson during a break.'})
        # Teacher clash: same teacher, same day+slot in another class.
        teacher = self.class_subject.teacher if self.class_subject_id else None
        if teacher and self.slot_id and self.day is not None:
            clash = Period.objects.filter(
                day=self.day, slot=self.slot, class_subject__teacher=teacher
            ).exclude(pk=self.pk).select_related('school_class').first()
            if clash:
                raise ValidationError(
                    f'{teacher} already teaches {clash.school_class} during {self.slot.name} on {self.get_day_display()}.'
                )
