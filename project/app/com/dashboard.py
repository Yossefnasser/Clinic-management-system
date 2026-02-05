from django.shortcuts import render
from app.models import Appointment, Doctor, Invoice, Patient
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum


@login_required
def dashboard(request):
    today = timezone.now().date()
    start_of_current_month = today.replace(day=1)

    # Previous month boundaries
    if start_of_current_month.month == 1:
        start_of_previous_month = start_of_current_month.replace(year=start_of_current_month.year - 1, month=12)
    else:
        start_of_previous_month = start_of_current_month.replace(month=start_of_current_month.month - 1)

    end_of_previous_month = start_of_current_month - timedelta(days=1)

    # --- Patients ---
    total_patients_count = Patient.objects.filter(branch=request.user.branch, deleted_date__isnull=True).count()
    patients_this_month = Patient.objects.filter(
        deleted_date__isnull=True,
        added_date__gte=start_of_current_month,
        added_date__lte=today
    ).count()
    patients_last_month = Patient.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        added_date__gte=start_of_previous_month,
        added_date__lte=end_of_previous_month
    ).count()
    if patients_last_month > 0:
        patients_growth_rate = ((patients_this_month - patients_last_month) / patients_last_month) * 100
    else:
        patients_growth_rate = 0

    # --- Appointments ---
    start_of_week = today - timedelta(days=today.weekday())  # Monday as start
    end_of_week = start_of_week + timedelta(days=6)
    appointments_this_week = Appointment.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        date__gte=start_of_week,
        date__lte=end_of_week
    ).count()
    appointments_today = Appointment.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        date=today
    ).count()

    # --- Doctors ---
    active_doctors_count = Doctor.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        is_active=True
    ).count()

    # --- Income ---
    total_income = Invoice.objects.filter(
        appointment__branch=request.user.branch,
        deleted_date__isnull=True
    ).aggregate(Sum("total_price"))["total_price__sum"] or 0

    # This week income
    income_this_week = Invoice.objects.filter(
        appointment__branch=request.user.branch,
        deleted_date__isnull=True,
        created_at__date__gte=start_of_week,
        created_at__date__lte=end_of_week
    ).aggregate(Sum("total_price"))["total_price__sum"] or 0

    # Last week income
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = start_of_week - timedelta(days=1)

    income_last_week = Invoice.objects.filter(
        appointment__branch=request.user.branch,
        deleted_date__isnull=True,
        created_at__date__gte=start_of_last_week,
        created_at__date__lte=end_of_last_week
    ).aggregate(Sum("total_price"))["total_price__sum"] or 0

    # Growth %
    if income_last_week > 0:
        income_growth_rate = ((income_this_week - income_last_week) / income_last_week) * 100
    else:
        income_growth_rate = 0

    context = {
        'total_patients_count': total_patients_count,
        'patients_this_month': patients_this_month,
        'patients_last_month': patients_last_month,
        'patients_growth_rate': round(patients_growth_rate, 2),

        'appointments_this_week': appointments_this_week,
        'appointments_today': appointments_today,
        'active_doctors_count': active_doctors_count,

        'total_income': total_income,
        'income_this_week': income_this_week,
        'income_last_week': income_last_week,
        'income_growth_rate': round(income_growth_rate, 2),
    }
    return render(request, 'dashboard.html', context)
