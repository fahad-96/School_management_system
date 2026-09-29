from .models import Mark, grade_for


def report_card(exam, student):
    """Per-subject rows plus totals for one student in one exam."""
    marks = {m.exam_subject_id: m for m in Mark.objects.filter(exam_subject__exam=exam, student=student)}
    rows, obtained, maximum = [], 0.0, 0.0
    for es in exam.subjects.select_related('subject'):
        mark = marks.get(es.pk)
        maximum += float(es.max_marks)
        if mark is not None:
            obtained += float(mark.score)
        rows.append({
            'subject': es.subject,
            'max_marks': es.max_marks,
            'pass_marks': es.pass_marks,
            'score': mark.score if mark else None,
            'percentage': mark.percentage if mark else None,
            'grade': mark.grade if mark else '-',
            'passed': mark.passed if mark else None,
            'remarks': mark.remarks if mark else '',
        })
    pct = round(obtained * 100 / maximum, 1) if maximum else 0.0
    return {
        'rows': rows,
        'obtained': obtained,
        'maximum': maximum,
        'percentage': pct,
        'grade': grade_for(pct) if rows else '-',
        'complete': all(r['score'] is not None for r in rows),
    }


def class_results(exam):
    """Ranked totals for every student in the exam's class."""
    subjects = list(exam.subjects.all())
    maximum = sum(float(es.max_marks) for es in subjects)
    totals = {}
    for m in Mark.objects.filter(exam_subject__exam=exam):
        totals[m.student_id] = totals.get(m.student_id, 0.0) + float(m.score)
    results = []
    for student in exam.school_class.students.select_related('user'):
        obtained = totals.get(student.pk, 0.0)
        pct = round(obtained * 100 / maximum, 1) if maximum else 0.0
        results.append({'student': student, 'obtained': obtained, 'percentage': pct, 'grade': grade_for(pct)})
    results.sort(key=lambda r: -r['obtained'])
    for i, r in enumerate(results, start=1):
        r['rank'] = i
    return {'results': results, 'maximum': maximum, 'subjects': subjects}


def student_rank(exam, student):
    for r in class_results(exam)['results']:
        if r['student'].pk == student.pk:
            return r['rank']
    return None
