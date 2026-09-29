from django.conf import settings
from django.db import models


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text='e.g. 2026-27')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)

    @classmethod
    def current(cls):
        return cls.objects.filter(is_current=True).first() or cls.objects.first()


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    qualification = models.CharField(max_length=200, blank=True)
    joined_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class SchoolClass(models.Model):
    name = models.CharField(max_length=50, help_text='e.g. Grade 5')
    section = models.CharField(max_length=10, default='A')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='classes')
    class_teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='classes_led'
    )
    room = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ['name', 'section']
        unique_together = ('name', 'section', 'academic_year')
        verbose_name_plural = 'classes'

    def __str__(self):
        return f'{self.name}-{self.section}'


class ClassSubject(models.Model):
    """A subject taught in a class, and the teacher responsible for it."""

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='class_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='class_subjects'
    )

    class Meta:
        ordering = ['subject__name']
        unique_together = ('school_class', 'subject')

    def __str__(self):
        return f'{self.school_class} · {self.subject}'


class Parent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    admission_no = models.CharField(max_length=20, unique=True)
    roll_no = models.PositiveIntegerField()
    school_class = models.ForeignKey(SchoolClass, on_delete=models.PROTECT, related_name='students')
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    address = models.TextField(blank=True)
    admitted_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['school_class', 'roll_no']
        unique_together = ('school_class', 'roll_no')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return str(self)
