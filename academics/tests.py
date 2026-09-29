from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .forms import StudentForm
from .models import Student
from .services import can_view_student, classes_for_teacher
from .testing import make_school


class StudentFormTests(TestCase):
    def setUp(self):
        self.s = make_school()

    def test_creates_user_and_student(self):
        form = StudentForm(data={
            'username': 'newkid', 'first_name': 'New', 'last_name': 'Kid', 'email': '', 'phone': '', 'password': 'secret123',
            'admission_no': 'A9', 'roll_no': 9, 'school_class': self.s.cls.pk, 'parent': '', 'date_of_birth': '',
            'gender': 'M', 'address': '', 'admitted_on': '',
        })
        self.assertTrue(form.is_valid(), form.errors)
        student = form.save()
        self.assertEqual(student.user.role, User.Role.STUDENT)
        self.assertTrue(student.user.check_password('secret123'))

    def test_rejects_duplicate_username(self):
        form = StudentForm(data={'username': 'student', 'first_name': 'X', 'password': 'x', 'admission_no': 'A9',
                                 'roll_no': 9, 'school_class': self.s.cls.pk})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_edit_keeps_password_when_blank(self):
        student = self.s.student
        form = StudentForm(instance=student, data={
            'username': 'student', 'first_name': 'Renamed', 'last_name': '', 'email': '', 'phone': '', 'password': '',
            'admission_no': 'A1', 'roll_no': 1, 'school_class': self.s.cls.pk, 'parent': self.s.parent.pk,
            'date_of_birth': '', 'gender': '', 'address': '', 'admitted_on': '',
        })
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        student.user.refresh_from_db()
        self.assertEqual(student.user.first_name, 'Renamed')
        self.assertTrue(student.user.check_password('pw'))


class ServiceTests(TestCase):
    def setUp(self):
        self.s = make_school()

    def test_classes_for_teacher_includes_led_and_taught(self):
        self.assertCountEqual(classes_for_teacher(self.s.teacher), [self.s.cls, self.s.other_cls])
        self.assertCountEqual(classes_for_teacher(self.s.other_teacher), [self.s.cls, self.s.other_cls])

    def test_can_view_student(self):
        s = self.s
        self.assertTrue(can_view_student(s.admin, s.stranger))
        self.assertTrue(can_view_student(s.teacher.user, s.student))
        self.assertTrue(can_view_student(s.student.user, s.student))
        self.assertFalse(can_view_student(s.student.user, s.student2))
        self.assertTrue(can_view_student(s.parent.user, s.student))
        self.assertFalse(can_view_student(s.parent.user, s.stranger))

    def test_student_detail_permission(self):
        self.client.login(username='student', password='pw')
        self.assertEqual(self.client.get(reverse('student_detail', args=[self.s.student.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_detail', args=[self.s.student2.pk])).status_code, 403)

    def test_deleting_student_removes_login(self):
        self.client.login(username='admin', password='pw')
        self.client.post(reverse('student_delete', args=[self.s.student2.pk]))
        self.assertFalse(Student.objects.filter(pk=self.s.student2.pk).exists())
        self.assertFalse(User.objects.filter(username='student2').exists())
