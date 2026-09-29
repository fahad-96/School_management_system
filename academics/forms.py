from django import forms
from django.core.exceptions import ValidationError

from accounts.forms import BootstrapFormMixin
from accounts.models import User

from .models import AcademicYear, ClassSubject, Parent, SchoolClass, Student, Subject, Teacher

USER_FIELDS = ('username', 'first_name', 'last_name', 'email', 'phone')


class UserProfileForm(BootstrapFormMixin, forms.ModelForm):
    """ModelForm for a profile model (Student/Teacher/Parent) that also creates/updates its login User."""

    role = None

    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    password = forms.CharField(
        widget=forms.PasswordInput, required=False,
        help_text='Leave blank to keep the current password.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            for name in USER_FIELDS:
                self.fields[name].initial = getattr(self.instance.user, name)
        else:
            self.fields['password'].required = True
            self.fields['password'].help_text = ''
        self.order_fields(list(USER_FIELDS) + ['password'] + [f for f in self.fields if f not in USER_FIELDS and f != 'password'])

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError('That username is already taken.')
        return username

    def save(self, commit=True):
        data = self.cleaned_data
        user = self.instance.user if self.instance.pk else User(role=self.role)
        for name in USER_FIELDS:
            setattr(user, name, data[name])
        if data.get('password'):
            user.set_password(data['password'])
        user.save()
        self.instance.user = user
        return super().save(commit=commit)


class StudentForm(UserProfileForm):
    role = User.Role.STUDENT

    class Meta:
        model = Student
        fields = ['admission_no', 'roll_no', 'school_class', 'parent', 'date_of_birth', 'gender', 'address', 'admitted_on']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}


class TeacherForm(UserProfileForm):
    role = User.Role.TEACHER

    class Meta:
        model = Teacher
        fields = ['employee_id', 'subjects', 'qualification', 'joined_on']


class ParentForm(UserProfileForm):
    role = User.Role.PARENT

    class Meta:
        model = Parent
        fields = ['occupation', 'address']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}


class SchoolClassForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'section', 'academic_year', 'class_teacher', 'room']


class SubjectForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code']


class AcademicYearForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']


class ClassSubjectForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ['subject', 'teacher']

    def __init__(self, *args, school_class=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school_class = school_class
        if school_class is not None:
            taken = school_class.class_subjects.values_list('subject_id', flat=True)
            self.fields['subject'].queryset = Subject.objects.exclude(pk__in=taken)

    def save(self, commit=True):
        self.instance.school_class = self.school_class
        return super().save(commit=commit)
