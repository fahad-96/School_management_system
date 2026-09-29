from django.db.models import Q

from .models import ClassSubject, SchoolClass


def classes_for_teacher(teacher):
    """Classes a teacher leads or teaches a subject in."""
    if teacher is None:
        return SchoolClass.objects.none()
    return SchoolClass.objects.filter(
        Q(class_teacher=teacher) | Q(class_subjects__teacher=teacher)
    ).distinct()


def classes_for_user(user):
    """Classes the user may manage (attendance, marks, reports)."""
    if user.is_admin:
        return SchoolClass.objects.all()
    if user.is_teacher:
        return classes_for_teacher(getattr(user, 'teacher', None))
    return SchoolClass.objects.none()


def teacher_manages_class(teacher, school_class):
    return classes_for_teacher(teacher).filter(pk=school_class.pk).exists()


def teacher_teaches(teacher, school_class, subject):
    if teacher is None:
        return False
    if school_class.class_teacher_id == teacher.pk:
        return True
    return ClassSubject.objects.filter(school_class=school_class, subject=subject, teacher=teacher).exists()


def can_manage_class(user, school_class):
    if user.is_admin:
        return True
    if user.is_teacher:
        return teacher_manages_class(getattr(user, 'teacher', None), school_class)
    return False


def can_view_student(user, student):
    """Admins see all; teachers see their classes; students themselves; parents their children."""
    if user.is_admin:
        return True
    if user.is_teacher:
        return teacher_manages_class(getattr(user, 'teacher', None), student.school_class)
    if user.is_student:
        return student.user_id == user.pk
    if user.is_parent:
        return student.parent is not None and student.parent.user_id == user.pk
    return False
