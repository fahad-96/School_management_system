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

## Deploy on Render (free)
The repo includes a Render Blueprint ([`render.yaml`](render.yaml)) with the build and start commands
and every setting, so nothing needs configuring by hand.

1. Sign in at [render.com](https://render.com) with GitHub.
2. Choose **New → Blueprint**, pick this repository and click **Apply**.
3. When the first deploy finishes, open the `onrender.com` address shown on the service page and sign in
   with the demo logins above.

Every push to `main` redeploys the site.

On the free plan:
- The site sleeps after 15 minutes without visitors, and the next visit takes up to a minute to wake it.
- There is no persistent disk. Each deploy builds a fresh SQLite database with the demo school, and every
  restart (including waking from sleep) starts from it again, so changes made on the live site are
  temporary. Real use needs the database somewhere permanent (a paid persistent disk or PostgreSQL),
  which takes a small settings change.
- The demo logins are public in this README, so anyone with the address can sign in. Use it for testing,
  not for real student data.

### Environment variables
Without these the app runs in local development mode. `render.yaml` sets them on Render.

| Variable | Production value |
|---|---|
| `DJANGO_DEBUG` | `0` |
| `DJANGO_SECRET_KEY` | A long random string (the Blueprint generates one) |
| `DJANGO_ALLOWED_HOSTS` | Your own domains, comma-separated. The `onrender.com` address is allowed automatically |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Only for a custom domain: `https://` and the domain, comma-separated |
| `DJANGO_TIME_ZONE` | Defaults to `Asia/Kolkata` |

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
render.yaml   Render deploy settings (build, start, environment)
```

## Notes
- The time zone defaults to `Asia/Kolkata` so "today" matches the school's clock; set `DJANGO_TIME_ZONE` (e.g. `UTC`) to change it.
