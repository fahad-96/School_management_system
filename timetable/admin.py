from django.contrib import admin

from .models import Period, TimeSlot


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'start_time', 'end_time', 'is_break')


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'day', 'slot', 'class_subject')
    list_filter = ('school_class', 'day')
