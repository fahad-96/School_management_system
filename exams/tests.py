from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from academics.testing import make_school

from .models import Exam, ExamSubject, Mark, grade_for
from .services import class_results, report_card


class ExamTests(TestCase):
    def setUp(self):
        self.s = make_school()
        self.exam = Exam.objects.create(name='Mid Term', school_class=self.s.cls,
                                        start_date=date(2026, 9, 1), end_date=date(2026, 9, 5))
        self.es_math = ExamSubject.objects.create(exam=self.exam, subject=self.s.math, max_marks=100)
        self.es_sci = ExamSubject.objects.create(exam=self.exam, subject=self.s.sci, max_marks=50)
        Mark.objects.create(exam_subject=self.es_math, student=self.s.student, score=Decimal('80'))
        Mark.objects.create(exam_subject=self.es_sci, student=self.s.student, score=Decimal('40'))
        Mark.objects.create(exam_subject=self.es_math, student=self.s.student2, score=Decimal('95'))
        Mark.objects.create(exam_subject=self.es_sci, student=self.s.student2, score=Decimal('45'))

    def test_grade_bands(self):
        self.assertEqual([grade_for(p) for p in (95, 85, 75, 65, 55, 45, 10)], ['A+', 'A', 'B+', 'B', 'C', 'D', 'F'])

    def test_report_card_totals(self):
        card = report_card(self.exam, self.s.student)
        self.assertEqual((card['obtained'], card['maximum'], card['percentage'], card['grade']), (120.0, 150.0, 80.0, 'A'))
        self.assertTrue(card['complete'])

    def test_class_results_ranked(self):
        results = class_results(self.exam)['results']
        self.assertEqual([r['student'] for r in results], [self.s.student2, self.s.student])
        self.assertEqual([r['rank'] for r in results], [1, 2])

    def test_student_sees_report_only_when_published(self):
        url = reverse('report_card', args=[self.exam.pk, self.s.student.pk])
        self.client.login(username='student', password='pw')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.exam.is_published = True
        self.exam.save()
        self.assertEqual(self.client.get(url).status_code, 200)
        # Cannot see a classmate's card.
        self.assertEqual(self.client.get(reverse('report_card', args=[self.exam.pk, self.s.student2.pk])).status_code, 403)

    def test_marks_entry_permissions_and_save(self):
        # other_teacher teaches Science in this class but not Maths, and isn't class teacher.
        self.client.login(username='teacher2', password='pw')
        self.assertEqual(self.client.get(reverse('marks_entry', args=[self.es_math.pk])).status_code, 403)
        r = self.client.post(reverse('marks_entry', args=[self.es_sci.pk]),
                             {f'score_{self.s.student.pk}': '33.5', f'score_{self.s.student2.pk}': ''})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Mark.objects.get(exam_subject=self.es_sci, student=self.s.student).score, Decimal('33.5'))
        self.assertFalse(Mark.objects.filter(exam_subject=self.es_sci, student=self.s.student2).exists())

    def test_marks_entry_rejects_out_of_range(self):
        self.client.login(username='admin', password='pw')
        r = self.client.post(reverse('marks_entry', args=[self.es_sci.pk]), {f'score_{self.s.student.pk}': '75'})
        self.assertEqual(r.status_code, 200)  # re-rendered with error
        self.assertEqual(Mark.objects.get(exam_subject=self.es_sci, student=self.s.student).score, Decimal('40'))
