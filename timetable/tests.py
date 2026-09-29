from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from academics.models import ClassSubject
from academics.testing import make_school

from .models import Period, TimeSlot
from .services import build_grid, class_periods


class TimetableTests(TestCase):
    def setUp(self):
        self.s = make_school()
        self.slot1 = TimeSlot.objects.create(name='P1', start_time=time(8, 0), end_time=time(8, 45), order=1)
        self.brk = TimeSlot.objects.create(name='Break', start_time=time(8, 45), end_time=time(9, 0), order=2, is_break=True)
        self.slot2 = TimeSlot.objects.create(name='P2', start_time=time(9, 0), end_time=time(9, 45), order=3)

    def test_teacher_clash_rejected(self):
        Period.objects.create(school_class=self.s.cls, day=0, slot=self.slot1, class_subject=self.s.cs_math)
        other_cs = ClassSubject.objects.get(school_class=self.s.other_cls, subject=self.s.math)  # same teacher
        clash = Period(school_class=self.s.other_cls, day=0, slot=self.slot1, class_subject=other_cs)
        with self.assertRaises(ValidationError):
            clash.full_clean()
        # Different slot is fine.
        Period(school_class=self.s.other_cls, day=0, slot=self.slot2, class_subject=other_cs).full_clean()

    def test_subject_must_belong_to_class(self):
        wrong = Period(school_class=self.s.other_cls, day=1, slot=self.slot1, class_subject=self.s.cs_math)
        with self.assertRaises(ValidationError):
            wrong.full_clean()

    def test_cannot_schedule_in_break(self):
        with self.assertRaises(ValidationError):
            Period(school_class=self.s.cls, day=1, slot=self.brk, class_subject=self.s.cs_math).full_clean()

    def test_grid_shape(self):
        Period.objects.create(school_class=self.s.cls, day=2, slot=self.slot2, class_subject=self.s.cs_sci)
        days, rows = build_grid(class_periods(self.s.cls))
        self.assertEqual(len(days), 6)
        self.assertEqual([r['slot'] for r in rows], [self.slot1, self.brk, self.slot2])
        self.assertEqual(rows[2]['cells'][2].class_subject, self.s.cs_sci)
        self.assertIsNone(rows[0]['cells'][2])

    def test_admin_adds_period_via_form_and_student_can_view(self):
        self.client.login(username='admin', password='pw')
        r = self.client.post(reverse('class_timetable', args=[self.s.cls.pk]),
                             {'day': 0, 'slot': self.slot1.pk, 'class_subject': self.s.cs_math.pk})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Period.objects.count(), 1)
        self.client.login(username='student', password='pw')
        self.assertEqual(self.client.get(reverse('class_timetable', args=[self.s.cls.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('class_timetable', args=[self.s.other_cls.pk])).status_code, 403)
