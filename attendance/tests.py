from datetime import date

from django.test import TestCase
from django.urls import reverse

from academics.testing import make_school

from .models import AttendanceRecord
from .services import student_attendance_summary, summarize


class AttendanceTests(TestCase):
    def setUp(self):
        self.s = make_school()
        self.day = date(2026, 9, 21)

    def _post(self, cls, extra):
        return self.client.post(reverse('attendance_mark'), {'school_class': cls.pk, 'date': self.day.isoformat(), **extra})

    def test_teacher_marks_own_class(self):
        self.client.login(username='teacher', password='pw')
        r = self._post(self.s.cls, {f'status_{self.s.student.pk}': 'A', f'status_{self.s.student2.pk}': 'P',
                                    f'remarks_{self.s.student.pk}': 'sick'})
        self.assertEqual(r.status_code, 302)
        rec = AttendanceRecord.objects.get(student=self.s.student, date=self.day)
        self.assertEqual((rec.status, rec.remarks, rec.marked_by), ('A', 'sick', self.s.teacher.user))
        # Re-posting updates rather than duplicates.
        self._post(self.s.cls, {f'status_{self.s.student.pk}': 'L'})
        self.assertEqual(AttendanceRecord.objects.filter(student=self.s.student).count(), 1)
        self.assertEqual(AttendanceRecord.objects.get(student=self.s.student).status, 'L')

    def test_teacher_cannot_mark_unrelated_class(self):
        # other_teacher teaches in cls, so make a class nobody but admin manages.
        from academics.models import SchoolClass
        lonely = SchoolClass.objects.create(name='Grade 9', section='A', academic_year=self.s.year)
        self.client.login(username='teacher', password='pw')
        self.assertEqual(self._post(lonely, {}).status_code, 403)

    def test_summary_percentage_counts_late_as_attended(self):
        for d, status in [(1, 'P'), (2, 'P'), (3, 'L'), (4, 'A')]:
            AttendanceRecord.objects.create(student=self.s.student, date=date(2026, 9, d), status=status)
        summary = student_attendance_summary(self.s.student)
        self.assertEqual(summary['total'], 4)
        self.assertEqual(summary['percentage'], 75.0)
        self.assertEqual(summarize([])['percentage'], 0.0)

    def test_student_report_visibility(self):
        self.client.login(username='parent', password='pw')
        self.assertEqual(self.client.get(reverse('attendance_student', args=[self.s.student.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('attendance_student', args=[self.s.stranger.pk])).status_code, 403)
