from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.permissions import ADMIN, STAFF, AdminRequiredMixin, StaffRequiredMixin, role_required
from attendance.services import student_attendance_summary
from exams.models import Exam
from fees.services import student_fee_summary

from .forms import (
    AcademicYearForm, ClassSubjectForm, ParentForm, SchoolClassForm, StudentForm, SubjectForm, TeacherForm,
)
from .models import AcademicYear, ClassSubject, Parent, SchoolClass, Student, Subject, Teacher
from .services import can_view_student, classes_for_user


# ---------- generic building blocks ----------

class BaseCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = 'academics/form.html'
    success_message = '%(name)s created.'

    def get_success_message(self, cleaned_data):
        return f'{self.model._meta.verbose_name.title()} saved.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Add {self.model._meta.verbose_name}'
        return ctx


class BaseUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = 'academics/form.html'

    def get_success_message(self, cleaned_data):
        return f'{self.model._meta.verbose_name.title()} saved.'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit {self.model._meta.verbose_name}'
        return ctx


class BaseDeleteView(AdminRequiredMixin, DeleteView):
    template_name = 'academics/confirm_delete.html'

    def form_valid(self, form):
        messages.success(self.request, f'{self.model._meta.verbose_name.title()} deleted.')
        return super().form_valid(form)


class ProfileDeleteView(BaseDeleteView):
    """Deleting a Student/Teacher/Parent also removes their login."""

    def form_valid(self, form):
        user = self.object.user
        response = super().form_valid(form)
        user.delete()
        return response


# ---------- students ----------

class StudentListView(StaffRequiredMixin, ListView):
    model = Student
    template_name = 'academics/student_list.html'
    paginate_by = 25

    def get_queryset(self):
        qs = Student.objects.select_related('user', 'school_class', 'parent__user')
        if not self.request.user.is_admin:
            qs = qs.filter(school_class__in=classes_for_user(self.request.user))
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
                | Q(admission_no__icontains=q) | Q(user__username__icontains=q)
            )
        cls = self.request.GET.get('class')
        if cls:
            qs = qs.filter(school_class_id=cls)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['classes'] = classes_for_user(self.request.user)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_class'] = self.request.GET.get('class', '')
        return ctx


@role_required(*STAFF, 'student', 'parent')
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('user', 'school_class', 'parent__user'), pk=pk)
    if not can_view_student(request.user, student):
        raise PermissionDenied
    exams = Exam.objects.filter(school_class=student.school_class)
    if not request.user.is_admin and not request.user.is_teacher:
        exams = exams.filter(is_published=True)
    return render(request, 'academics/student_detail.html', {
        'student': student,
        'attendance': student_attendance_summary(student),
        'fees': student_fee_summary(student),
        'exams': exams,
    })


class StudentCreateView(BaseCreateView):
    model = Student
    form_class = StudentForm
    success_url = reverse_lazy('student_list')


class StudentUpdateView(BaseUpdateView):
    model = Student
    form_class = StudentForm

    def get_success_url(self):
        return reverse_lazy('student_detail', kwargs={'pk': self.object.pk})


class StudentDeleteView(ProfileDeleteView):
    model = Student
    success_url = reverse_lazy('student_list')


# ---------- teachers ----------

class TeacherListView(StaffRequiredMixin, ListView):
    model = Teacher
    template_name = 'academics/teacher_list.html'
    queryset = Teacher.objects.select_related('user').prefetch_related('subjects')


@role_required(*STAFF)
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher.objects.select_related('user'), pk=pk)
    return render(request, 'academics/teacher_detail.html', {
        'teacher': teacher,
        'classes_led': teacher.classes_led.select_related('academic_year'),
        'assignments': teacher.class_subjects.select_related('school_class', 'subject'),
    })


class TeacherCreateView(BaseCreateView):
    model = Teacher
    form_class = TeacherForm
    success_url = reverse_lazy('teacher_list')


class TeacherUpdateView(BaseUpdateView):
    model = Teacher
    form_class = TeacherForm
    success_url = reverse_lazy('teacher_list')


class TeacherDeleteView(ProfileDeleteView):
    model = Teacher
    success_url = reverse_lazy('teacher_list')


# ---------- parents ----------

class ParentListView(AdminRequiredMixin, ListView):
    model = Parent
    template_name = 'academics/parent_list.html'
    queryset = Parent.objects.select_related('user').prefetch_related('children__user', 'children__school_class')


class ParentCreateView(BaseCreateView):
    model = Parent
    form_class = ParentForm
    success_url = reverse_lazy('parent_list')


class ParentUpdateView(BaseUpdateView):
    model = Parent
    form_class = ParentForm
    success_url = reverse_lazy('parent_list')


class ParentDeleteView(ProfileDeleteView):
    model = Parent
    success_url = reverse_lazy('parent_list')


# ---------- classes ----------

class SchoolClassListView(StaffRequiredMixin, ListView):
    model = SchoolClass
    template_name = 'academics/class_list.html'

    def get_queryset(self):
        return classes_for_user(self.request.user).select_related('academic_year', 'class_teacher__user')


@role_required(*STAFF)
def class_detail(request, pk):
    school_class = get_object_or_404(SchoolClass.objects.select_related('academic_year', 'class_teacher__user'), pk=pk)
    if not request.user.is_admin and school_class not in classes_for_user(request.user):
        raise PermissionDenied
    form = ClassSubjectForm(school_class=school_class)
    if request.method == 'POST':
        if not request.user.is_admin:
            raise PermissionDenied
        form = ClassSubjectForm(request.POST, school_class=school_class)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject assigned.')
            return redirect('class_detail', pk=pk)
    return render(request, 'academics/class_detail.html', {
        'school_class': school_class,
        'students': school_class.students.select_related('user'),
        'class_subjects': school_class.class_subjects.select_related('subject', 'teacher__user'),
        'form': form,
    })


class SchoolClassCreateView(BaseCreateView):
    model = SchoolClass
    form_class = SchoolClassForm
    success_url = reverse_lazy('class_list')


class SchoolClassUpdateView(BaseUpdateView):
    model = SchoolClass
    form_class = SchoolClassForm

    def get_success_url(self):
        return reverse_lazy('class_detail', kwargs={'pk': self.object.pk})


class SchoolClassDeleteView(BaseDeleteView):
    model = SchoolClass
    success_url = reverse_lazy('class_list')


@role_required(ADMIN)
def class_subject_delete(request, pk):
    cs = get_object_or_404(ClassSubject, pk=pk)
    if request.method == 'POST':
        cs.delete()
        messages.success(request, 'Subject removed from class.')
    return redirect('class_detail', pk=cs.school_class_id)


# ---------- subjects & years ----------

class SubjectListView(StaffRequiredMixin, ListView):
    model = Subject
    template_name = 'academics/subject_list.html'


class SubjectCreateView(BaseCreateView):
    model = Subject
    form_class = SubjectForm
    success_url = reverse_lazy('subject_list')


class SubjectUpdateView(BaseUpdateView):
    model = Subject
    form_class = SubjectForm
    success_url = reverse_lazy('subject_list')


class SubjectDeleteView(BaseDeleteView):
    model = Subject
    success_url = reverse_lazy('subject_list')


class AcademicYearListView(AdminRequiredMixin, ListView):
    model = AcademicYear
    template_name = 'academics/year_list.html'


class AcademicYearCreateView(BaseCreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    success_url = reverse_lazy('year_list')


class AcademicYearUpdateView(BaseUpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    success_url = reverse_lazy('year_list')


class AcademicYearDeleteView(BaseDeleteView):
    model = AcademicYear
    success_url = reverse_lazy('year_list')
