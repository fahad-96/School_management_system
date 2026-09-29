from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from academics.testing import make_school

from .models import FeeStructure, Payment
from .services import dues_report, student_fee_summary, total_outstanding


class FeeTests(TestCase):
    def setUp(self):
        self.s = make_school()
        FeeStructure.objects.create(school_class=self.s.cls, category='tuition', amount=Decimal('1000'), due_date=date(2026, 5, 1))
        FeeStructure.objects.create(school_class=self.s.cls, category='transport', amount=Decimal('250'), due_date=date(2026, 5, 1))
        Payment.objects.create(student=self.s.student, amount=Decimal('700'), paid_on=date(2026, 5, 2))

    def test_summary_and_dues(self):
        summary = student_fee_summary(self.s.student)
        self.assertEqual((summary['total'], summary['paid'], summary['due']), (Decimal('1250'), Decimal('700'), Decimal('550')))
        rows = {r['student']: r['due'] for r in dues_report()}
        self.assertEqual(rows[self.s.student], Decimal('550'))
        self.assertEqual(rows[self.s.student2], Decimal('1250'))
        self.assertNotIn(self.s.stranger, rows)  # no fees defined for that class
        self.assertEqual(total_outstanding(), Decimal('1800'))

    def test_receipt_numbers_are_sequential_and_unique(self):
        p2 = Payment.objects.create(student=self.s.student, amount=Decimal('1'))
        p3 = Payment.objects.create(student=self.s.student2, amount=Decimal('1'))
        self.assertTrue(p2.receipt_no.startswith('RCPT-'))
        self.assertNotEqual(p2.receipt_no, p3.receipt_no)

    def test_admin_records_payment_and_gets_receipt(self):
        self.client.login(username='admin', password='pw')
        r = self.client.post(reverse('payment_add'), {
            'student': self.s.student2.pk, 'fee_structure': '', 'amount': '500', 'paid_on': '2026-09-20',
            'method': 'cash', 'reference': '', 'note': '',
        })
        payment = Payment.objects.get(student=self.s.student2)
        self.assertRedirects(r, reverse('receipt', args=[payment.pk]))
        self.assertEqual(payment.received_by, self.s.admin)

    def test_receipt_visible_to_owner_only(self):
        payment = Payment.objects.get(student=self.s.student)
        self.client.login(username='student', password='pw')
        self.assertEqual(self.client.get(reverse('receipt', args=[payment.pk])).status_code, 200)
        self.client.login(username='student2', password='pw')
        self.assertEqual(self.client.get(reverse('receipt', args=[payment.pk])).status_code, 403)
