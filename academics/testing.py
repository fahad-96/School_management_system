"""Shared fixture builder for the test suites."""
from datetime import date
from types import SimpleNamespace

from accounts.models import User

from .models import AcademicYear, ClassSubject, Parent, SchoolClass, Student, Subject, Teacher


def make_school():
    admin = User.objects.create_user('admin', password='pw', role='admin')
    year = AcademicYear.objects.create(name='2026-27', start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    math = Subject.objects.create(name='Mathematics', code='MATH')
    sci = Subject.objects.create(name='Science', code='SCI')

    teacher = Teacher.objects.create(user=User.objects.create_user('teacher', password='pw', role='teacher'), employee_id='EMP1')
    other_teacher = Teacher.objects.create(user=User.objects.create_user('teacher2', password='pw', role='teacher'), employee_id='EMP2')

    cls = SchoolClass.objects.create(name='Grade 5', section='A', academic_year=year, class_teacher=teacher)
    other_cls = SchoolClass.objects.create(name='Grade 6', section='A', academic_year=year, class_teacher=other_teacher)
    cs_math = ClassSubject.objects.create(school_class=cls, subject=math, teacher=teacher)
    cs_sci = ClassSubject.objects.create(school_class=cls, subject=sci, teacher=other_teacher)
    ClassSubject.objects.create(school_class=other_cls, subject=math, teacher=teacher)

    parent = Parent.objects.create(user=User.objects.create_user('parent', password='pw', role='parent'))
    student = Student.objects.create(user=User.objects.create_user('student', password='pw', role='student'),
                                     admission_no='A1', roll_no=1, school_class=cls, parent=parent)
    student2 = Student.objects.create(user=User.objects.create_user('student2', password='pw', role='student'),
                                      admission_no='A2', roll_no=2, school_class=cls)
    stranger = Student.objects.create(user=User.objects.create_user('stranger', password='pw', role='student'),
                                      admission_no='A3', roll_no=1, school_class=other_cls)
    return SimpleNamespace(
        admin=admin, year=year, math=math, sci=sci, teacher=teacher, other_teacher=other_teacher,
        cls=cls, other_cls=other_cls, cs_math=cs_math, cs_sci=cs_sci, parent=parent,
        student=student, student2=student2, stranger=stranger,
    )
