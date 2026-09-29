from django.test import TestCase
from django.urls import reverse

from academics.testing import make_school


class RoleAccessTests(TestCase):
    def setUp(self):
        self.s = make_school()

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(reverse('dashboard'))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_each_role_gets_its_dashboard(self):
        for username, template in [('admin', 'accounts/dashboard_admin.html'), ('teacher', 'accounts/dashboard_teacher.html'),
                                   ('student', 'accounts/dashboard_student.html'), ('parent', 'accounts/dashboard_student.html')]:
            self.client.login(username=username, password='pw')
            r = self.client.get(reverse('dashboard'))
            self.assertEqual(r.status_code, 200, username)
            self.assertTemplateUsed(r, template)
            self.client.logout()

    def test_student_cannot_open_staff_pages(self):
        self.client.login(username='student', password='pw')
        for name in ('student_list', 'attendance_mark', 'payment_list', 'teacher_list'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_teacher_cannot_open_admin_only_pages(self):
        self.client.login(username='teacher', password='pw')
        for name in ('parent_list', 'payment_list', 'fee_structure_list', 'student_add'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_parent_child_switcher(self):
        self.client.login(username='parent', password='pw')
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.context['student'], self.s.student)
        # Switching to a child that isn't theirs falls back to their own child.
        r = self.client.get(reverse('dashboard'), {'child': self.s.stranger.pk})
        self.assertEqual(r.context['student'], self.s.student)
