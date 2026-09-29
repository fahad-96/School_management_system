from django.contrib import admin

from .models import Exam, ExamSubject, Mark


class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 0


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_class', 'start_date', 'end_date', 'is_published')
    list_filter = ('school_class', 'is_published')
    inlines = [ExamSubjectInline]


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam_subject', 'score')
    list_filter = ('exam_subject__exam',)
    search_fields = ('student__user__first_name', 'student__user__last_name')
