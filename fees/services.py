from decimal import Decimal

from django.db.models import Sum

from academics.models import Student

from .models import FeeStructure, Payment

ZERO = Decimal('0.00')


def student_fee_summary(student):
    structures = FeeStructure.objects.filter(school_class=student.school_class)
    payments = Payment.objects.filter(student=student).select_related('fee_structure', 'received_by')
    total = structures.aggregate(s=Sum('amount'))['s'] or ZERO
    paid = payments.aggregate(s=Sum('amount'))['s'] or ZERO
    return {
        'structures': structures,
        'payments': payments,
        'total': total,
        'paid': paid,
        'due': total - paid,
    }


def dues_report(only_outstanding=True):
    """[{student, total, paid, due}] across all students."""
    class_totals = {
        row['school_class']: row['s']
        for row in FeeStructure.objects.values('school_class').annotate(s=Sum('amount'))
    }
    paid_by_student = {
        row['student']: row['s']
        for row in Payment.objects.values('student').annotate(s=Sum('amount'))
    }
    rows = []
    for student in Student.objects.select_related('user', 'school_class'):
        total = class_totals.get(student.school_class_id, ZERO)
        paid = paid_by_student.get(student.pk, ZERO)
        due = total - paid
        if only_outstanding and due <= 0:
            continue
        rows.append({'student': student, 'total': total, 'paid': paid, 'due': due})
    rows.sort(key=lambda r: -r['due'])
    return rows


def total_outstanding():
    return sum((r['due'] for r in dues_report()), ZERO)
