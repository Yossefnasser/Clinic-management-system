# Clinic Management System (CMS)

A comprehensive Django-based clinic management system designed to streamline appointment scheduling, patient management, doctor profiles, and clinic operations.

## Features

- **User Management**: Role-based user system (Admin, Manager, Secretary)
- **Doctor Management**: Create and manage doctor profiles with specializations and pricing
- **Patient Management**: Store and manage patient information and medical history
- **Appointment Scheduling**: Book and manage patient appointments with doctors
- **Doctor Schedules**: Create and manage doctor availability and time slots
- **Authentication**: Secure login system with JWT token support
- **REST API**: Django REST Framework integration for API endpoints
- **Admin Dashboard**: Comprehensive admin interface for system management

## Tech Stack

- **Backend**: Django 5.2.4
- **Database**: PostgreSQL (production) / SQLite (development)
- **API**: Django REST Framework 3.16.0, Simple JWT 5.5.1
- **Server**: Gunicorn 23.0.0
- **ORM**: SQLAlchemy 2.0.41 (for migrations and data operations)
- **Web Server**: WhiteNoise 6.11.0 (static file serving)

## Project Structure

```
project/
├── app/                          # Main application
│   ├── models.py                # Database models (User, Doctor, Patient, Appointment, etc.)
│   ├── views.py                 # View functions and logic
│   ├── urls.py                  # URL routing
│   ├── admin.py                 # Django admin configuration
│   ├── helpers.py               # Utility functions
│   ├── com/                     # Communication/business logic modules
│   │   ├── appointment.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── doctors.py
│   │   ├── patient.py
│   │   └── users.py
│   ├── management/              # Custom Django commands
│   │   └── commands/
│   │       └── create_clinic_slots.py
│   ├── migrations/              # Database migrations
│   ├── templates/               # HTML templates
│   └── templatetags/            # Custom template tags
├── project/                     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── db.sqlite3                  # SQLite database (development)
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL (for production)
- pip or conda package manager

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CMS
```

### 2. Create Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run Migrations

```bash
cd project
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Available Management Commands

### Create Clinic Slots

Generate doctor appointment slots:

```bash
python manage.py create_clinic_slots
```

## Models Overview

### User
Extended Django User model with role-based access:
- **User Types**: Manager, Admin, Secretary
- Fields: fullname, phone_number, user_type, is_active

### Doctor
Manages doctor information:
- Full name, specialization, contact details
- Pricing for consultations and examinations
- Active/inactive status

### Patient
Stores patient information:
- Name, phone number, age, gender
- Medical notes and history

### Appointment
Manages patient appointments:
- Links patients to doctors
- Tracks appointment status and pricing
- Records date/time and service type

### DoctorSchedule
Manages doctor availability:
- Working hours and days
- Break times and time slots

### Specialization
Categorizes doctors by medical specialty

## API Endpoints

The system includes REST API endpoints for:
- Authentication (JWT tokens)
- User management
- Doctor management
- Patient management
- Appointment booking
- Schedule management

## Database

### Development
SQLite database (`db.sqlite3`)

### Production
PostgreSQL with environment configuration via `DATABASE_URL`

## Deployment

### Using Procfile (Heroku/similar platforms)

```bash
release: cd project && python manage.py migrate
web: cd project && gunicorn project.wsgi:application --bind 0.0.0.0:8000
```

### Environment Setup for Production

Set these environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Set to False
- `SECRET_KEY`: Strong random key
- `ALLOWED_HOSTS`: Your domain names

## Static Files

Run collectstatic to gather all static files:

```bash
cd project
python manage.py collectstatic
```

## Common Tasks

### Creating a Clinic Specialization

```python
from app.models import Specialization

Specialization.objects.create(name="Cardiology")
```

### Adding a Doctor

```python
from app.models import Doctor, Specialization

spec = Specialization.objects.get(name="Cardiology")
doctor = Doctor.objects.create(
    full_name="Dr. John Doe",
    specialization=spec,
    phone_number="123-456-7890",
    email="john@example.com",
    examination_price=50.00,
    consultation_price=30.00
)
```

### Booking an Appointment

```python
from app.models import Appointment, Patient, Doctor

patient = Patient.objects.get(pk=1)
doctor = Doctor.objects.get(pk=1)
appointment = Appointment.objects.create(
    patient=patient,
    doctor=doctor,
    appointment_date="2026-01-15",
    appointment_time="10:00"
)
```

## Troubleshooting

### Database Migration Issues

Reset migrations (development only):
```bash
cd project
python manage.py migrate app zero
python manage.py migrate app
```

### Static Files Not Loading

Ensure WhiteNoise is installed and configured:
```bash
pip install whitenoise
python manage.py collectstatic
```

### Port Already in Use

Run on a different port:
```bash
python manage.py runserver 8001
```

## Testing

Run the test suite:

```bash
cd project
python manage.py test
```

## Contributing

1. Create a feature branch
2. Commit your changes
3. Push to the branch
4. Create a Pull Request

## Support

For issues or questions, please contact the development team or open an issue in the repository.

## Changelog

### Version 1.0.0
- Initial release
- Core functionality for appointment scheduling
- Doctor and patient management
- User authentication
- Admin dashboard
