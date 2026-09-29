# School Management System

A role-based school management web app built with **Django 6 + SQLite** and Bootstrap 5.

## Modules
| Module | What it does |
|---|---|
| Academics | Academic years, subjects, classes/sections, teachers, students, parents, subject–teacher assignments per class |
| Attendance | Mark a whole class per day (Present / Absent / Late), monthly class report, per-student history |
| Exams & grades | Exams per class, per-subject max/pass marks, marks entry grid, ranked results, printable report cards (A+ … F) |
| Fees | Fee structure per class, record payments with auto receipt numbers, printable receipts, statements, dues report |
| Timetable | Time slots, weekly grid per class and per teacher, teacher double-booking prevented |

## Roles
| Role | Can do |
|---|---|
| **Admin** | Everything (custom UI + Django admin at `/admin/`) |
| **Teacher** | View their classes/students, mark attendance, enter marks for subjects they teach, see their timetable |
| **Student** | View own attendance, published results, fee statement, timetable |
| **Parent** | Same as student, for each linked child (switcher in the top bar) |

## Run it
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # optional demo data + logins
python manage.py runserver
```
Open http://127.0.0.1:8000/

### Demo logins (after `seed_demo`)
| Username | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| teacher1 | teacher123 | Teacher (class teacher of Grade 5-A) |
| student1 | student123 | Student |
| parent1 | parent123 | Parent of student1 |

To start with an empty school instead, skip `seed_demo` and run `python manage.py createsuperuser`.

## Tests
```bash
python manage.py test
```

## Project layout
```
config/       settings + root urls
accounts/     custom User (role field), login, dashboards, role permissions, seed_demo command
academics/    years, subjects, classes, teachers, students, parents
attendance/   daily attendance + reports
exams/        exams, marks, report cards
fees/         fee structure, payments, receipts, dues
timetable/    time slots, periods, weekly grids
templates/    Bootstrap templates (base.html has the sidebar)
static/css/   small custom stylesheet
```

## Notes
- `TIME_ZONE` in `config/settings.py` is `UTC`; change it to your local zone (e.g. `Asia/Kolkata`) so "today" matches your clock.
- Before deploying, set these environment variables: `DJANGO_SECRET_KEY` (a long random string), `DJANGO_DEBUG=0`, and `DJANGO_ALLOWED_HOSTS` (comma-separated, e.g. `school.example.com`). Without them the app runs in local development mode.
