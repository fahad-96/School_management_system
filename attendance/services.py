from .models import AttendanceRecord


def summarize(records):
    """Counts + percentage for an iterable/queryset of AttendanceRecord."""
    counts = {'P': 0, 'A': 0, 'L': 0}
    for record in records:
        counts[record.status] = counts.get(record.status, 0) + 1
    total = sum(counts.values())
    attended = counts['P'] + counts['L']
    return {
        'total': total,
        'present': counts['P'],
        'absent': counts['A'],
        'late': counts['L'],
        'percentage': round(attended * 100 / total, 1) if total else 0.0,
    }


def student_attendance_summary(student, start=None, end=None):
    qs = AttendanceRecord.objects.filter(student=student)
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return summarize(qs)


def class_attendance_for_date(school_class, date):
    """{student_id: AttendanceRecord} for one class on one day."""
    return {
        r.student_id: r
        for r in AttendanceRecord.objects.filter(student__school_class=school_class, date=date)
    }
