# Clinic Management System (CMS)

Clinic Management System is a Django 5.2 application for managing clinics with an Arabic RTL UI. It supports multi-branch operations, role-based users, doctors, patients, schedules, appointments, and revenue dashboards.

## Highlights

- **RTL Arabic UI** built with Bootstrap 5 RTL, DataTables, and SweetAlert2.
- **Role-based users** (Manager, Admin, Secretary).
- **Doctors & patients** with branch-level separation.
- **Clinics, slots, and schedules** for doctor availability.
- **Appointments & invoices** with dashboard analytics.
- **JSON endpoints** for AJAX-driven screens.
- **Railway-ready** configuration with WhiteNoise + Gunicorn.

## Tech Stack

- **Backend**: Django 5.2.4, Django REST Framework 3.16.0
- **Database**: SQLite (local) / PostgreSQL via `DATABASE_PUBLIC_URL` (Railway)
- **Frontend**: Bootstrap 5 RTL, DataTables, SweetAlert2, Font Awesome
- **Static**: WhiteNoise 6.11.0
- **Server**: Gunicorn 23.0.0

## Project Layout

```
project/
├── app/                          # Django app
│   ├── com/                      # Feature modules (auth, dashboard, doctors, patient, appointment, users)
│   ├── management/commands/      # Custom commands
│   ├── migrations/
│   ├── templates/                # HTML templates (RTL)
│   ├── templatetags/
│   ├── models.py
│   ├── urls.py
│   └── admin.py
├── project/                      # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                       # Project static assets
├── staticfiles/                  # collectstatic output
└── manage.py
```

## Quick Start (Local)

1) Create and activate a virtual environment.
2) Install dependencies.
3) Run migrations and create a superuser.
4) Start the server.

> Note: `manage.py` lives inside the project folder. Run commands from the project directory.

```
cd project
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open: http://localhost:8000

## Configuration Notes

- **Database**: local uses SQLite by default. For Railway or other managed Postgres, set `DATABASE_PUBLIC_URL`.
- **Security**: `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are enabled. For local HTTP development, set them to `False` in [project/settings.py](project/settings.py).
- **Allowed hosts**: currently `['*']` in settings for development; restrict in production.

## Required Seed Data

Some screens expect initial records to exist:

- **Branch**: create at least one branch.
- **Status**: create `OPEN` and `Completed` (used in appointments and invoices).
- **Days of Week**: add 7 records.
- **Clinics** and **Specializations**: for schedules and appointments.

Example (Django shell):

```
from app.models import Branch, Status, DaysOfWeek, Clinic, Specialization

branch = Branch.objects.create(address="Main Branch")
Status.objects.get_or_create(name="OPEN")
Status.objects.get_or_create(name="Completed")
for d in ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]:
    DaysOfWeek.objects.get_or_create(name=d)

Specialization.objects.get_or_create(name="Cardiology")
Clinic.objects.get_or_create(name="General Clinic", branch=branch)
```

## Management Commands

- `create_clinic_slots`: regenerate 1-hour slots per clinic.
- `set_default_branch`: set `branch_id=1` for existing records missing a branch.

```
cd project
python manage.py create_clinic_slots
python manage.py set_default_branch
```

## JSON Endpoints (AJAX)

These routes return JSON for the UI (login required):

- `/api/time-slots/`
- `/api/doctors/<doctor_id>/latest-appointments/`
- `/api/patients/<patient_id>/latest-appointments/`
- `/api/new-appointment`
- `/api/clinics/<clinic_id>/time-slots/`
- `/api/clinics/<clinic_id>/schedule/`
- `/api/get-doctors-by-specialization`
- `/api/get-doctor-schedule`

## Deployment (Procfile)

```
release: cd project && python manage.py migrate
web: cd project && gunicorn project.wsgi:application --bind 0.0.0.0:8000
```

## Static Files

```
cd project
python manage.py collectstatic
```

## Testing

```
cd project
python manage.py test
```

## Contributing

1. Create a feature branch.
2. Commit your changes.
3. Push the branch and open a PR.

## Changelog

### 1.0.0
- Initial release: core scheduling, doctors, patients, and dashboard.
