from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import SchoolClass, Student


class FeeStructure(models.Model):
    class Category(models.TextChoices):
        TUITION = 'tuition', 'Tuition'
        TRANSPORT = 'transport', 'Transport'
        LIBRARY = 'library', 'Library'
        LAB = 'lab', 'Laboratory'
        EXAM = 'exam', 'Examination'
        OTHER = 'other', 'Other'

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='fee_structures')
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.TUITION)
    description = models.CharField(max_length=200, blank=True, help_text='e.g. Term 1')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    class Meta:
        ordering = ['due_date', 'category']

    def __str__(self):
        label = self.get_category_display()
        return f'{label} {self.description}'.strip() + f' ({self.school_class})'


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'cash', 'Cash'
        CARD = 'card', 'Card'
        BANK = 'bank', 'Bank transfer'
        UPI = 'upi', 'UPI'
        CHEQUE = 'cheque', 'Cheque'

    receipt_no = models.CharField(max_length=20, unique=True, editable=False)
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='payments')
    fee_structure = models.ForeignKey(
        FeeStructure, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments',
        help_text='Optional: which fee this payment is for',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=100, blank=True, help_text='Transaction / cheque number')
    note = models.CharField(max_length=200, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_on', '-id']

    def __str__(self):
        return f'{self.receipt_no} · {self.student} · {self.amount}'

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            last = Payment.objects.order_by('-id').values_list('id', flat=True).first() or 0
            self.receipt_no = f'RCPT-{last + 1:06d}'
        super().save(*args, **kwargs)
