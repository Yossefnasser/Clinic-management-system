from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from app.models import PrintJob  # the model you'll add


def print_display(request):
    return render(request, 'printing/print_display.html')


@require_GET
def print_jobs_pending(request):
    job = PrintJob.objects.filter(status='pending').order_by('created_at').first()

    if not job:
        return JsonResponse({"job": None})

    appointment = job.appointment

    return JsonResponse({
        "job": {
            "id": job.id,
            "display_number": job.id,
            "clinic_name": appointment.clinic.name,
            "doctor_name": appointment.doctor.full_name,
            "appointment_time
