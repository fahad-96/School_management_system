from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.helpers import get_current_student
from accounts.permissions import ADMIN, ALL, STAFF, role_required
from academics.models import Student
from academics.services import can_manage_class, can_view_student, classes_for_user, teacher_teaches

from .forms import ExamForm, ExamSubjectForm
from .models import Exam, ExamSubject, Mark
from .services import class_results, report_card, student_rank


def _can_enter_marks(user, exam_subject):
    if user.is_admin:
        return True
    if user.is_teacher:
        return teacher_teaches(getattr(user, 'teacher', None), exam_subject.exam.school_class, exam_subject.subject)
    return False


@role_required(*ALL)
def exam_list(request):
    user = request.user
    if user.is_admin or user.is_teacher:
        exams = Exam.objects.filter(school_class__in=classes_for_user(user))
    else:
        student = get_current_student(request)
        if student is None:
            return render(request, 'accounts/no_profile.html')
        exams = Exam.objects.filter(school_class=student.school_class, is_published=True)
    return render(request, 'exams/exam_list.html', {
        'exams': exams.select_related('school_class').prefetch_related('subjects'),
    })


@role_required(ADMIN)
def exam_create(request):
    form = ExamForm(request.POST or None)
    if form.is_valid():
        exam = form.save()
        messages.success(request, 'Exam created. Now add its subjects.')
        return redirect('exam_detail', pk=exam.pk)
    return render(request, 'academics/form.html', {'form': form, 'title': 'Add exam'})


@role_required(ADMIN)
def exam_edit(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    form = ExamForm(request.POST or None, instance=exam)
    if form.is_valid():
        form.save()
        messages.success(request, 'Exam saved.')
        return redirect('exam_detail', pk=exam.pk)
    return render(request, 'academics/form.html', {'form': form, 'title': 'Edit exam'})


@role_required(ADMIN)
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.')
        return redirect('exam_list')
    return render(request, 'academics/confirm_delete.html', {'object': exam})


@role_required(*ALL)
def exam_detail(request, pk):
    exam = get_object_or_404(Exam.objects.select_related('school_class'), pk=pk)
    user = request.user
    student = None
    if user.is_admin or user.is_teacher:
        if not can_manage_class(user, exam.school_class):
            raise PermissionDenied
    else:
        student = get_current_student(request)
        if student is None or student.school_class_id != exam.school_class_id or not exam.is_published:
            raise PermissionDenied
        return redirect('report_card', pk=exam.pk, student_pk=student.pk)

    form = ExamSubjectForm(exam=exam)
    if request.method == 'POST':
        if not user.is_admin:
            raise PermissionDenied
        form = ExamSubjectForm(request.POST, exam=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added to exam.')
            return redirect('exam_detail', pk=pk)

    subjects = list(exam.subjects.select_related('subject'))
    for es in subjects:
        es.can_enter = _can_enter_marks(user, es)
        es.entered = es.marks.count()
    return render(request, 'exams/exam_detail.html', {
        'exam': exam,
        'subjects': subjects,
        'form': form,
        'results': class_results(exam),
        'student_count': exam.school_class.students.count(),
    })


@role_required(ADMIN)
def exam_subject_delete(request, pk):
    es = get_object_or_404(ExamSubject, pk=pk)
    if request.method == 'POST':
        es.delete()
        messages.success(request, 'Subject removed from exam.')
    return redirect('exam_detail', pk=es.exam_id)


@role_required(*STAFF)
def marks_entry(request, pk):
    es = get_object_or_404(ExamSubject.objects.select_related('exam__school_class', 'subject'), pk=pk)
    if not _can_enter_marks(request.user, es):
        raise PermissionDenied
    students = list(es.exam.school_class.students.select_related('user'))
    existing = {m.student_id: m for m in es.marks.all()}

    if request.method == 'POST':
        errors = []
        for s in students:
            raw = request.POST.get(f'score_{s.pk}', '').strip()
            remarks = request.POST.get(f'remarks_{s.pk}', '')[:200]
            if raw == '':
                if s.pk in existing:
                    existing[s.pk].delete()
                continue
            try:
                score = Decimal(raw)
            except InvalidOperation:
                errors.append(f'{s}: "{raw}" is not a number.')
                continue
            if score < 0 or score > es.max_marks:
                errors.append(f'{s}: score must be between 0 and {es.max_marks}.')
                continue
            Mark.objects.update_or_create(
                exam_subject=es, student=s, defaults={'score': score, 'remarks': remarks}
            )
        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            messages.success(request, f'Marks saved for {es.subject}.')
            return redirect('exam_detail', pk=es.exam_id)
        existing = {m.student_id: m for m in es.marks.all()}

    for s in students:
        m = existing.get(s.pk)
        s.score = request.POST.get(f'score_{s.pk}', m.score if m else '') if request.method == 'POST' else (m.score if m else '')
        s.remarks = m.remarks if m else ''
    return render(request, 'exams/marks_entry.html', {'es': es, 'students': students})


@role_required(*ALL)
def report_card_view(request, pk, student_pk):
    exam = get_object_or_404(Exam.objects.select_related('school_class'), pk=pk)
    student = get_object_or_404(Student.objects.select_related('user', 'school_class'), pk=student_pk)
    if not can_view_student(request.user, student):
        raise PermissionDenied
    if not (request.user.is_admin or request.user.is_teacher) and not exam.is_published:
        raise PermissionDenied
    return render(request, 'exams/report_card.html', {
        'exam': exam,
        'student': student,
        'card': report_card(exam, student),
        'rank': student_rank(exam, student),
        'today': timezone.localdate(),
    })


@role_required('student', 'parent')
def my_results(request):
    student = get_current_student(request)
    if student is None:
        return render(request, 'accounts/no_profile.html')
    exams = Exam.objects.filter(school_class=student.school_class, is_published=True)
    results = [(exam, report_card(exam, student)) for exam in exams]
    return render(request, 'exams/my_results.html', {'student': student, 'results': results})
