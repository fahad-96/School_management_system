from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.helpers import get_current_student
from accounts.permissions import ADMIN, ALL, STAFF, role_required
from academics.models import SchoolClass, Teacher
from academics.services import can_manage_class

from .forms import PeriodForm, TimeSlotForm
from .models import Period, TimeSlot
from .services import build_grid, class_periods, teacher_periods


@role_required(*ALL)
def class_timetable(request, pk):
    school_class = get_object_or_404(SchoolClass.objects.select_related('class_teacher__user'), pk=pk)
    user = request.user
    if user.is_student or user.is_parent:
        student = get_current_student(request)
        if student is None or student.school_class_id != school_class.pk:
            raise PermissionDenied
    elif not can_manage_class(user, school_class):
        raise PermissionDenied

    form = PeriodForm(school_class=school_class) if user.is_admin else None
    if request.method == 'POST':
        if not user.is_admin:
            raise PermissionDenied
        form = PeriodForm(request.POST, school_class=school_class)
        if form.is_valid():
            form.save()
            messages.success(request, 'Period added.')
            return redirect('class_timetable', pk=pk)

    days, rows = build_grid(class_periods(school_class))
    return render(request, 'timetable/grid.html', {
        'title': f'Timetable · {school_class}',
        'school_class': school_class,
        'days': days,
        'rows': rows,
        'form': form,
        'show_teacher': True,
    })


@role_required(*STAFF)
def teacher_timetable(request, pk):
    teacher = get_object_or_404(Teacher.objects.select_related('user'), pk=pk)
    if request.user.is_teacher and getattr(request.user, 'teacher', None) != teacher:
        raise PermissionDenied
    days, rows = build_grid(teacher_periods(teacher))
    return render(request, 'timetable/grid.html', {
        'title': f'Timetable · {teacher}',
        'teacher': teacher,
        'days': days,
        'rows': rows,
        'show_class': True,
    })


@role_required(*ALL)
def my_timetable(request):
    user = request.user
    if user.is_teacher:
        teacher = getattr(user, 'teacher', None)
        if teacher is None:
            return render(request, 'accounts/no_profile.html')
        return redirect('teacher_timetable', pk=teacher.pk)
    if user.is_admin:
        return redirect('class_list')
    student = get_current_student(request)
    if student is None:
        return render(request, 'accounts/no_profile.html')
    return redirect('class_timetable', pk=student.school_class_id)


@role_required(ADMIN)
def period_delete(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if request.method == 'POST':
        period.delete()
        messages.success(request, 'Period removed.')
    return redirect('class_timetable', pk=period.school_class_id)


@role_required(ADMIN)
def slot_list(request):
    return render(request, 'timetable/slot_list.html', {'slots': TimeSlot.objects.all()})


@role_required(ADMIN)
def slot_create(request):
    form = TimeSlotForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Time slot added.')
        return redirect('slot_list')
    return render(request, 'academics/form.html', {'form': form, 'title': 'Add time slot'})


@role_required(ADMIN)
def slot_edit(request, pk):
    slot = get_object_or_404(TimeSlot, pk=pk)
    form = TimeSlotForm(request.POST or None, instance=slot)
    if form.is_valid():
        form.save()
        messages.success(request, 'Time slot saved.')
        return redirect('slot_list')
    return render(request, 'academics/form.html', {'form': form, 'title': 'Edit time slot'})


@role_required(ADMIN)
def slot_delete(request, pk):
    slot = get_object_or_404(TimeSlot, pk=pk)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Time slot deleted.')
        return redirect('slot_list')
    return render(request, 'academics/confirm_delete.html', {'object': slot})
