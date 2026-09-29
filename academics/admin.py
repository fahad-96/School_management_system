from django.contrib import admin

from .models import AcademicYear, ClassSubject, Parent, SchoolClass, Student, Subject, Teacher


class ClassSubjectInline(admin.TabularInline):
    model = ClassSubject
    extra = 0


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'employee_id', 'joined_on')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id')
    filter_horizontal = ('subjects',)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'academic_year', 'class_teacher', 'room')
    list_filter = ('academic_year',)
    inlines = [ClassSubjectInline]


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'occupation')
    search_fields = ('user__first_name', 'user__last_name')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'admission_no', 'roll_no', 'school_class', 'parent')
    list_filter = ('school_class',)
    search_fields = ('user__first_name', 'user__last_name', 'admission_no')
