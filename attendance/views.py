import calendar
from datetime import date

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.helpers import get_current_student
from accounts.permissions import ALL, STAFF, role_required
from academics.models import SchoolClass, Student
from academics.services import can_manage_class, can_view_student, classes_for_user

from .forms import AttendanceSelectForm, MonthSelectForm
from .models import AttendanceRecord
from .services import class_attendance_for_date, summarize


@role_required(*STAFF)
def mark_attendance(request):
    classes = classes_for_user(request.user)
    form = AttendanceSelectForm(request.GET or None, classes=classes)
    school_class = selected_date = None
    students = []
    if form.is_valid():
        school_class = form.cleaned_data['school_class']
        selected_date = form.cleaned_data['date']
        existing = class_attendance_for_date(school_class, selected_date)
        students = list(school_class.students.select_related('user'))
        for s in students:
            record = existing.get(s.pk)
            s.current_status = record.status if record else 'P'
            s.current_remarks = record.remarks if record else ''

    if request.method == 'POST':
        school_class = get_object_or_404(SchoolClass, pk=request.POST.get('school_class'))
        selected_date = date.fromisoformat(request.POST.get('date'))
        if not can_manage_class(request.user, school_class):
            raise PermissionDenied
        saved = 0
        for student in school_class.students.all():
            status = request.POST.get(f'status_{student.pk}')
            if status not in AttendanceRecord.Status.values:
                continue
            AttendanceRecord.objects.update_or_create(
                student=student, date=selected_date,
                defaults={
                    'status': status,
                    'remarks': request.POST.get(f'remarks_{student.pk}', '')[:200],
                    'marked_by': request.user,
                },
            )
            saved += 1
        messages.success(request, f'Attendance saved for {saved} students ({school_class}, {selected_date}).')
        return redirect(f"{request.path}?school_class={school_class.pk}&date={selected_date.isoformat()}")

    return render(request, 'attendance/mark.html', {
        'form': form,
        'school_class': school_class,
        'date': selected_date,
        'students': students,
        'statuses': AttendanceRecord.Status.choices,
    })


@role_required(*STAFF)
def class_report(request):
    classes = classes_for_user(request.user)
    today = timezone.localdate()
    initial = {'month': today.strftime('%Y-%m')}
    form = MonthSelectForm(request.GET or None, classes=classes, initial=initial)
    context = {'form': form}
    if form.is_valid():
        school_class = form.cleaned_data['school_class']
        year, month = (int(x) for x in form.cleaned_data['month'].split('-'))
        days_in_month = calendar.monthrange(year, month)[1]
        records = AttendanceRecord.objects.filter(
            student__school_class=school_class, date__year=year, date__month=month
        )
        marked_days = sorted({r.date.day for r in records})
        by_student = {}
        for r in records:
            by_student.setdefault(r.student_id, {})[r.date.day] = r.status
        rows = []
        for s in school_class.students.select_related('user'):
            statuses = by_student.get(s.pk, {})
            rows.append({
                'student': s,
                'cells': [statuses.get(d, '') for d in marked_days],
                'summary': summarize(records.filter(student=s)),
            })
        context.update({
            'school_class': school_class,
            'month_label': date(year, month, 1).strftime('%B %Y'),
            'days': marked_days,
            'rows': rows,
            'days_in_month': days_in_month,
            'overall': summarize(records),
        })
    return render(request, 'attendance/class_report.html', context)


@role_required(*ALL)
def student_report(request, pk):
    student = get_object_or_404(Student.objects.select_related('user', 'school_class'), pk=pk)
    if not can_view_student(request.user, student):
        raise PermissionDenied
    records = AttendanceRecord.objects.filter(student=student).select_related('marked_by')
    month = request.GET.get('month')
    if month:
        year, mon = (int(x) for x in month.split('-'))
        records = records.filter(date__year=year, date__month=mon)
    return render(request, 'attendance/student_report.html', {
        'student': student,
        'records': records,
        'summary': summarize(records),
        'month': month or '',
    })


@role_required('student', 'parent')
def my_attendance(request):
    student = get_current_student(request)
    if student is None:
        return render(request, 'accounts/no_profile.html')
    return redirect('attendance_student', pk=student.pk)
