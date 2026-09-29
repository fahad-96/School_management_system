from django.contrib import admin

from .models import FeeStructure, Payment


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'category', 'description', 'amount', 'due_date')
    list_filter = ('school_class', 'category')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'student', 'amount', 'paid_on', 'method', 'received_by')
    list_filter = ('method', 'paid_on')
    search_fields = ('receipt_no', 'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('receipt_no',)
