from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.helpers import get_current_student
from accounts.permissions import ADMIN, ALL, role_required
from academics.models import Student
from academics.services import can_view_student

from .forms import FeeStructureForm, PaymentForm
from .models import FeeStructure, Payment
from .services import dues_report, student_fee_summary


@role_required(ADMIN)
def structure_list(request):
    structures = FeeStructure.objects.select_related('school_class')
    return render(request, 'fees/structure_list.html', {'structures': structures})


@role_required(ADMIN)
def structure_create(request):
    form = FeeStructureForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Fee added.')
        return redirect('fee_structure_list')
    return render(request, 'academics/form.html', {'form': form, 'title': 'Add fee'})


@role_required(ADMIN)
def structure_edit(request, pk):
    obj = get_object_or_404(FeeStructure, pk=pk)
    form = FeeStructureForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Fee saved.')
        return redirect('fee_structure_list')
    return render(request, 'academics/form.html', {'form': form, 'title': 'Edit fee'})


@role_required(ADMIN)
def structure_delete(request, pk):
    obj = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Fee deleted.')
        return redirect('fee_structure_list')
    return render(request, 'academics/confirm_delete.html', {'object': obj})


@role_required(ADMIN)
def payment_list(request):
    payments = Payment.objects.select_related('student__user', 'student__school_class', 'received_by')
    q = request.GET.get('q', '').strip()
    if q:
        payments = payments.filter(
            Q(receipt_no__icontains=q) | Q(student__user__first_name__icontains=q)
            | Q(student__user__last_name__icontains=q) | Q(student__admission_no__icontains=q)
        )
    return render(request, 'fees/payment_list.html', {'payments': payments[:200], 'q': q})


@role_required(ADMIN)
def payment_create(request):
    initial = {}
    if request.GET.get('student'):
        initial['student'] = get_object_or_404(Student, pk=request.GET['student'])
    form = PaymentForm(request.POST or None, initial=initial)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.received_by = request.user
        payment.save()
        messages.success(request, f'Payment recorded. Receipt {payment.receipt_no}.')
        return redirect('receipt', pk=payment.pk)
    return render(request, 'academics/form.html', {'form': form, 'title': 'Record payment'})


@role_required(*ALL)
def receipt(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related('student__user', 'student__school_class', 'fee_structure', 'received_by'), pk=pk
    )
    if not can_view_student(request.user, payment.student):
        raise PermissionDenied
    return render(request, 'fees/receipt.html', {'payment': payment})


@role_required(*ALL)
def student_statement(request, pk):
    student = get_object_or_404(Student.objects.select_related('user', 'school_class'), pk=pk)
    if not can_view_student(request.user, student):
        raise PermissionDenied
    return render(request, 'fees/statement.html', {'student': student, 'fees': student_fee_summary(student)})


@role_required('student', 'parent')
def my_fees(request):
    student = get_current_student(request)
    if student is None:
        return render(request, 'accounts/no_profile.html')
    return redirect('fee_statement', pk=student.pk)


@role_required(ADMIN)
def dues(request):
    show_all = request.GET.get('all') == '1'
    rows = dues_report(only_outstanding=not show_all)
    return render(request, 'fees/dues_report.html', {
        'rows': rows,
        'show_all': show_all,
        'total_due': sum(r['due'] for r in rows),
    })
