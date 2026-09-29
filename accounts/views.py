from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone

from academics.models import SchoolClass, Student, Subject, Teacher
from academics.services import classes_for_teacher
from attendance.models import AttendanceRecord
from attendance.services import student_attendance_summary, summarize
from exams.models import Exam
from exams.services import report_card
from fees.models import Payment
from fees.services import student_fee_summary, total_outstanding
from timetable.services import class_periods, periods_today, teacher_periods

from .forms import ChangePasswordForm, LoginForm
from .helpers import get_current_student


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class UserPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('dashboard')
    success_message = 'Password updated.'


@login_required
def dashboard(request):
    user = request.user
    if user.is_admin:
        return admin_dashboard(request)
    if user.is_teacher:
        return teacher_dashboard(request)
    return student_dashboard(request)


def admin_dashboard(request):
    today = timezone.localdate()
    today_records = AttendanceRecord.objects.filter(date=today)
    month_collected = Payment.objects.filter(
        paid_on__year=today.year, paid_on__month=today.month
    ).aggregate(s=Sum('amount'))['s'] or 0
    context = {
        'student_count': Student.objects.count(),
        'teacher_count': Teacher.objects.count(),
        'class_count': SchoolClass.objects.count(),
        'subject_count': Subject.objects.count(),
        'attendance_today': summarize(today_records),
        'month_collected': month_collected,
        'total_outstanding': total_outstanding(),
        'recent_payments': Payment.objects.select_related('student__user')[:5],
        'upcoming_exams': Exam.objects.filter(end_date__gte=today).select_related('school_class').order_by('start_date')[:5],
        'today': today,
    }
    return render(request, 'accounts/dashboard_admin.html', context)


def teacher_dashboard(request):
    teacher = getattr(request.user, 'teacher', None)
    if teacher is None:
        return render(request, 'accounts/no_profile.html')
    today = timezone.localdate()
    classes = list(classes_for_teacher(teacher).select_related('academic_year', 'class_teacher'))
    marked_today = set(
        AttendanceRecord.objects.filter(date=today, student__school_class__in=classes)
        .values_list('student__school_class_id', flat=True)
    )
    for c in classes:
        c.marked_today = c.pk in marked_today
    context = {
        'teacher': teacher,
        'classes': classes,
        'today': today,
        'periods_today': periods_today(teacher_periods(teacher), today),
        'upcoming_exams': Exam.objects.filter(school_class__in=classes, end_date__gte=today).order_by('start_date')[:5],
    }
    return render(request, 'accounts/dashboard_teacher.html', context)


def student_dashboard(request):
    student = get_current_student(request)
    if student is None:
        return render(request, 'accounts/no_profile.html')
    today = timezone.localdate()
    exams = Exam.objects.filter(school_class=student.school_class, is_published=True)[:3]
    results = [(exam, report_card(exam, student)) for exam in exams]
    fees = student_fee_summary(student)
    context = {
        'student': student,
        'today': today,
        'attendance': student_attendance_summary(student),
        'results': results,
        'fees': fees,
        'periods_today': periods_today(class_periods(student.school_class), today),
    }
    return render(request, 'accounts/dashboard_student.html', context)
