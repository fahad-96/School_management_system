"""Populate the database with a small demo school. Safe to re-run (skips if data exists)."""
import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from academics.models import AcademicYear, ClassSubject, Parent, SchoolClass, Student, Subject, Teacher
from accounts.models import User
from attendance.models import AttendanceRecord
from exams.models import Exam, ExamSubject, Mark
from fees.models import FeeStructure, Payment
from timetable.models import Period, TimeSlot

FIRST_NAMES = ['Aarav', 'Diya', 'Ishaan', 'Meera', 'Kabir', 'Anaya', 'Rohan', 'Sara', 'Vihaan', 'Zara',
               'Arjun', 'Naina', 'Dev', 'Kiara', 'Reyansh', 'Myra', 'Aditya', 'Riya', 'Yash', 'Tara']
LAST_NAMES = ['Sharma', 'Khan', 'Patel', 'Singh', 'Nair', 'Bhat', 'Mehta', 'Rao', 'Das', 'Iyer']


class Command(BaseCommand):
    help = 'Create demo users, classes, students, attendance, exams, fees and a timetable.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Seed even if students already exist.')

    @transaction.atomic
    def handle(self, *args, **options):
        if Student.objects.exists() and not options['force']:
            self.stdout.write(self.style.WARNING('Students already exist; skipping. Use --force to add anyway.'))
            return
        random.seed(42)
        today = timezone.localdate()

        # --- admin ---
        admin, created = User.objects.get_or_create(
            username='admin', defaults={'first_name': 'School', 'last_name': 'Admin', 'role': User.Role.ADMIN,
                                        'is_staff': True, 'is_superuser': True, 'email': 'admin@example.com'})
        if created:
            admin.set_password('admin123')
            admin.save()

        # --- year, subjects ---
        year, _ = AcademicYear.objects.get_or_create(
            name=f'{today.year}-{str(today.year + 1)[-2:]}',
            defaults={'start_date': date(today.year, 4, 1), 'end_date': date(today.year + 1, 3, 31), 'is_current': True})
        subjects = {}
        for name, code in [('Mathematics', 'MATH'), ('Science', 'SCI'), ('English', 'ENG'),
                           ('Social Studies', 'SST'), ('Computer Science', 'CS')]:
            subjects[code], _ = Subject.objects.get_or_create(code=code, defaults={'name': name})

        # --- teachers ---
        teacher_specs = [
            ('teacher1', 'Priya', 'Menon', ['MATH', 'CS']),
            ('teacher2', 'Rahul', 'Verma', ['SCI']),
            ('teacher3', 'Anita', 'Joseph', ['ENG', 'SST']),
        ]
        teachers = []
        for i, (username, first, last, codes) in enumerate(teacher_specs, start=1):
            user = self._user(username, first, last, User.Role.TEACHER, 'teacher123')
            teacher, _ = Teacher.objects.get_or_create(
                user=user, defaults={'employee_id': f'EMP{i:03d}', 'joined_on': today - timedelta(days=400 * i),
                                     'qualification': 'B.Ed'})
            teacher.subjects.set([subjects[c] for c in codes])
            teachers.append(teacher)

        # --- classes + subject assignments ---
        classes = []
        for idx, (name, section, lead) in enumerate([('Grade 5', 'A', teachers[0]), ('Grade 6', 'A', teachers[1])]):
            cls, _ = SchoolClass.objects.get_or_create(
                name=name, section=section, academic_year=year,
                defaults={'class_teacher': lead, 'room': f'R{101 + idx}'})
            classes.append(cls)
            for code, teacher in [('MATH', teachers[0]), ('CS', teachers[0]), ('SCI', teachers[1]),
                                  ('ENG', teachers[2]), ('SST', teachers[2])]:
                ClassSubject.objects.get_or_create(school_class=cls, subject=subjects[code], defaults={'teacher': teacher})

        # --- parents + students ---
        students = []
        counter = 0
        for cls in classes:
            for roll in range(1, 11):
                counter += 1
                first = FIRST_NAMES[(counter - 1) % len(FIRST_NAMES)]
                last = LAST_NAMES[(counter - 1) % len(LAST_NAMES)]
                p_user = self._user(f'parent{counter}', f'{random.choice(["Mr", "Mrs"])} {last}', 'Family',
                                    User.Role.PARENT, 'parent123', phone=f'98{counter:08d}')
                parent, _ = Parent.objects.get_or_create(user=p_user, defaults={'occupation': 'Engineer'})
                s_user = self._user(f'student{counter}', first, last, User.Role.STUDENT, 'student123')
                student, _ = Student.objects.get_or_create(
                    user=s_user,
                    defaults={'admission_no': f'ADM{today.year}{counter:03d}', 'roll_no': roll, 'school_class': cls,
                              'parent': parent, 'gender': random.choice(['M', 'F']),
                              'date_of_birth': date(today.year - 11 - classes.index(cls), random.randint(1, 12), random.randint(1, 28)),
                              'admitted_on': year.start_date})
                students.append(student)

        # --- time slots + timetable ---
        slot_specs = [('Period 1', 8, 0, 8, 45, False), ('Period 2', 8, 45, 9, 30, False), ('Break', 9, 30, 9, 50, True),
                      ('Period 3', 9, 50, 10, 35, False), ('Period 4', 10, 35, 11, 20, False), ('Period 5', 11, 20, 12, 5, False)]
        slots = []
        for order, (name, sh, sm, eh, em, brk) in enumerate(slot_specs, start=1):
            slot, _ = TimeSlot.objects.get_or_create(
                order=order, defaults={'name': name, 'start_time': time(sh, sm), 'end_time': time(eh, em), 'is_break': brk})
            slots.append(slot)
        lesson_slots = [s for s in slots if not s.is_break]
        codes = ['MATH', 'SCI', 'ENG', 'SST', 'CS']
        for ci, cls in enumerate(classes):
            cs_by_code = {cs.subject.code: cs for cs in cls.class_subjects.select_related('subject')}
            for day in range(5):
                for si, slot in enumerate(lesson_slots):
                    # Offset per class so the same teacher is never double-booked.
                    code = codes[(day + si + ci * 2) % len(codes)]
                    Period.objects.get_or_create(school_class=cls, day=day, slot=slot,
                                                 defaults={'class_subject': cs_by_code[code]})

        # --- attendance for the last 15 school days ---
        day = today
        school_days = 0
        while school_days < 15:
            if day.weekday() < 5:
                for s in students:
                    status = random.choices(['P', 'A', 'L'], weights=[88, 8, 4])[0]
                    AttendanceRecord.objects.get_or_create(
                        student=s, date=day, defaults={'status': status, 'marked_by': s.school_class.class_teacher.user})
                school_days += 1
            day -= timedelta(days=1)

        # --- exams + marks ---
        for cls in classes:
            exam, _ = Exam.objects.get_or_create(
                name='Mid Term', school_class=cls,
                defaults={'start_date': today - timedelta(days=30), 'end_date': today - timedelta(days=24), 'is_published': True})
            for i, cs in enumerate(cls.class_subjects.all()):
                es, _ = ExamSubject.objects.get_or_create(
                    exam=exam, subject=cs.subject,
                    defaults={'max_marks': 100, 'pass_marks': 33, 'exam_date': exam.start_date + timedelta(days=i)})
                for s in cls.students.all():
                    Mark.objects.get_or_create(exam_subject=es, student=s,
                                               defaults={'score': Decimal(random.randint(28, 98))})
            Exam.objects.get_or_create(
                name='Final Term', school_class=cls,
                defaults={'start_date': today + timedelta(days=45), 'end_date': today + timedelta(days=52)})

        # --- fees + some payments ---
        for cls in classes:
            for cat, desc, amount, months in [('tuition', 'Term 1', 15000, -2), ('tuition', 'Term 2', 15000, 3),
                                              ('transport', 'Annual', 6000, -2), ('exam', 'Annual', 1500, 1)]:
                FeeStructure.objects.get_or_create(
                    school_class=cls, category=cat, description=desc,
                    defaults={'amount': Decimal(amount), 'due_date': today + timedelta(days=30 * months)})
        for s in students:
            paid = random.choice([0, 15000, 21000, 37500])
            if paid:
                Payment.objects.create(student=s, amount=Decimal(paid), method=random.choice(['cash', 'upi', 'bank']),
                                       paid_on=today - timedelta(days=random.randint(1, 40)), received_by=admin,
                                       note='Demo payment')

        self.stdout.write(self.style.SUCCESS(
            'Demo data created.\n'
            '  admin / admin123        (Admin)\n'
            '  teacher1 / teacher123   (Teacher – class teacher of Grade 5-A)\n'
            '  student1 / student123   (Student in Grade 5-A)\n'
            '  parent1 / parent123     (Parent of student1)'
        ))

    @staticmethod
    def _user(username, first, last, role, password, phone=''):
        user, created = User.objects.get_or_create(
            username=username, defaults={'first_name': first, 'last_name': last, 'role': role, 'phone': phone,
                                         'email': f'{username}@example.com'})
        if created:
            user.set_password(password)
            user.save()
        return user
