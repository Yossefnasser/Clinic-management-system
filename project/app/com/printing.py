from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from app.models import PrintJob  # the model you'll add


def print_display(request):
    return render(request, 'printing/print_display.html')


@require_GET
def print_jobs_pending(request):
    # return the oldest pending print job (or null)
    job = PrintJob.objects.filter(status='pending').order_by('created_at').first()

    if not job:
        return JsonResponse({"job": None})

    appointment = job.appointment

    display_number = appointment.ticket_number if getattr(appointment, 'ticket_number', None) else job.id

    return JsonResponse({
        "job": {
            "id": job.id,
            "appointment_id": appointment.id,
            "display_number": display_number,
            "ticket_number": appointment.ticket_number,
            "clinic_name": appointment.clinic.name if appointment.clinic else None,
            "doctor_name": appointment.doctor.full_name if appointment.doctor else None,
            "appointment_date": appointment.date.strftime('%Y-%m-%d') if appointment.date else None,
            "appointment_time": appointment.time.strftime('%H:%M') if appointment.time else "",
            "patient_name": appointment.patient.name if appointment.patient else None,
            "patient_phone": appointment.patient.phone_number if appointment.patient else None,
            "service_price": str(appointment.service_price),
            "created_at": job.created_at.isoformat(),
        }
    })


@csrf_exempt
@require_POST
def mark_print_job_done(request, job_id=None):
    """Mark a print job as done. Accepts form/json with `job_id` or `id`.

    This endpoint is CSRF-exempt for local agent convenience.
    """
    # job_id may be provided via the URL path or in the POST body (form/json)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
    except Exception:
        payload = {}

    body_job_id = request.POST.get('job_id') or request.POST.get('id') or payload.get('job_id') or payload.get('id')
    job_id = job_id or body_job_id
    if not job_id:
        return JsonResponse({'success': False, 'error': 'job_id required'}, status=400)

    try:
        job = PrintJob.objects.get(id=job_id)
    except PrintJob.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'job not found'}, status=404)

    job.status = 'done'
    job.save()
    return JsonResponse({'success': True})
