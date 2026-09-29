from django.contrib import admin

from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date', 'student__school_class')
    search_fields = ('student__user__first_name', 'student__user__last_name')
