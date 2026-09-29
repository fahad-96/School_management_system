from .models import DAYS, Period, TimeSlot


def build_grid(periods):
    """Rows = time slots, columns = days. Returns (days, rows) where each row is
    {'slot': TimeSlot, 'cells': [Period|None per day]}."""
    lookup = {(p.slot_id, p.day): p for p in periods}
    rows = []
    for slot in TimeSlot.objects.all():
        rows.append({'slot': slot, 'cells': [lookup.get((slot.pk, day)) for day, _ in DAYS]})
    return DAYS, rows


def class_periods(school_class):
    return Period.objects.filter(school_class=school_class).select_related(
        'slot', 'class_subject__subject', 'class_subject__teacher__user'
    )


def teacher_periods(teacher):
    return Period.objects.filter(class_subject__teacher=teacher).select_related(
        'slot', 'school_class', 'class_subject__subject'
    )


def periods_today(periods, today):
    """Filter a period queryset to today's weekday (Sunday returns nothing)."""
    return periods.filter(day=today.weekday()).order_by('slot__order')
