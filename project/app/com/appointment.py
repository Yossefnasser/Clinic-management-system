from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from app.templatetags.helpers import get_id_of_object, merge_continuous_slots
from app.helpers import get_local_now, parse_time
from app.models import Appointment, Clinic, ClinicSlot, DailyStats, Doctor, DoctorSchedule, Patient, ScheduleStats, Status, User ,Specialization , DaysOfWeek
from django.db.models import Q, Sum, Count
import json

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
def list_of_appointments(request):
    days_of_week = DaysOfWeek.objects.filter(deleted_date__isnull=True)
    clinics = Clinic.objects.filter(branch=request.user.branch, deleted_date__isnull=True)
    schedules_data = DoctorSchedule.objects.filter(branch=request.user.branch, deleted_date__isnull=True)
    specializations = Specialization.objects.filter(deleted_date__isnull=True)
    context = {
        'clinics'             : clinics,
        'days_of_week'          : days_of_week,
        'specializations' :specializations
    }
    return render(request, 'appointment/list.html',context)

@login_required
def today_appointments(request):
    local_now = get_local_now()
    selected_date_str = request.GET.get("date")
    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date() if selected_date_str else local_now.date()
    except ValueError:
        selected_date = local_now.date()
        selected_date_str = None
    today = selected_date
    base_queryset = Appointment.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        date=today,
    )

    selected_doctor_id = request.GET.get("doctor")
    selected_clinic_id = request.GET.get("clinic")
    selected_start = request.GET.get("start")
    selected_end = request.GET.get("end")
    selected_specialization_id = request.GET.get("specialization")
    if not selected_specialization_id or selected_specialization_id == "None":
        selected_specialization_id = None

    appointments = base_queryset

    day_name_map_ar = [
        "الاثنين",
        "الثلاثاء",
        "الاربعاء",
        "الخميس",
        "الجمعة",
        "السبت",
        "الاحد",
    ]
    day_name_map_en = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    weekday_index = today.weekday()
    day_name_candidates = [
        day_name_map_ar[weekday_index],
        day_name_map_en[weekday_index],
    ]
    day_obj = DaysOfWeek.objects.filter(name__in=day_name_candidates).first()

    schedules = DoctorSchedule.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        is_active=True,
    )
    if day_obj:
        schedules = schedules.filter(day_of_week=day_obj)
    if selected_specialization_id:
        schedules = schedules.filter(doctor__specialization_id=selected_specialization_id)

    now_time = local_now.time()
    now_minutes = now_time.hour * 60 + now_time.minute
    is_current_day = today == local_now.date()
    is_past_day = today < local_now.date()
    is_future_day = today > local_now.date()
    schedule_slots = []
    for schedule in schedules.select_related("doctor", "clinic", "day_of_week"):
        slots = schedule.clinic_slot.all().order_by("start_time")
        merged_slots = merge_continuous_slots(slots)
        for start_time, end_time in merged_slots:
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            if is_current_day:
                is_active_now = start_minutes <= now_minutes <= end_minutes
                is_past = now_minutes > end_minutes
                is_upcoming = now_minutes < start_minutes
            elif is_past_day:
                is_active_now = False
                is_past = True
                is_upcoming = False
            else:
                is_active_now = False
                is_past = False
                is_upcoming = True
            schedule_slots.append(
                {
                    "doctor_id": schedule.doctor_id,
                    "clinic_id": schedule.clinic_id,
                    "doctor_name": schedule.doctor.full_name,
                    "specialization_name": schedule.doctor.specialization.name if schedule.doctor.specialization else "",
                    "clinic_name": schedule.clinic.name,
                    "consultation_price": schedule.doctor.consultation_price,
                    "examination_price": schedule.doctor.examination_price,
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_active": is_active_now,
                    "is_past": is_past,
                    "is_upcoming": is_upcoming,
                }
            )

    selected_start_time = parse_time(selected_start)
    selected_end_time = parse_time(selected_end)

    if selected_doctor_id:
        appointments = appointments.filter(doctor_id=selected_doctor_id)
    if selected_clinic_id:
        appointments = appointments.filter(clinic_id=selected_clinic_id)
    if selected_specialization_id:
        appointments = appointments.filter(doctor__specialization_id=selected_specialization_id)
    if selected_start_time and selected_end_time:
        appointments = appointments.filter(
            time__gte=selected_start_time,
            time__lt=selected_end_time,
        )

    appointments = appointments.select_related("patient", "doctor", "clinic", "status").order_by("time")

    paid_statuses = ["ARRIVED", "COMPLETED"]
    day_agg = appointments.filter(status__name__in=paid_statuses).aggregate(
        total=Sum("service_price"),
        patients=Count("id"),
    )
    day_total_revenue = day_agg["total"] or 0
    day_total_patients = day_agg["patients"] or 0

    daily_stats, _ = DailyStats.objects.get_or_create(
        branch=request.user.branch,
        date=today,
        defaults={
            "total_revenue": day_total_revenue,
            "total_patients": day_total_patients,
        },
    )
    if daily_stats.total_revenue != day_total_revenue or daily_stats.total_patients != day_total_patients:
        daily_stats.total_revenue = day_total_revenue
        daily_stats.total_patients = day_total_patients
        daily_stats.save()

    schedule_revenue = None
    schedule_patients_count = None
    if selected_start_time and selected_end_time and selected_doctor_id and selected_clinic_id:
        schedule_qs = Appointment.objects.filter(
            branch=request.user.branch,
            deleted_date__isnull=True,
            date=today,
            doctor_id=selected_doctor_id,
            time__gte=selected_start_time,
            time__lt=selected_end_time,
            status__name__in=paid_statuses,
        )
        schedule_qs = schedule_qs.filter(clinic_id=selected_clinic_id)
        schedule_agg = schedule_qs.aggregate(
            total=Sum("service_price"),
            patients=Count("id"),
        )
        schedule_revenue = schedule_agg["total"] or 0
        schedule_patients_count = schedule_agg["patients"] or 0

        schedule_stats, _ = ScheduleStats.objects.get_or_create(
            branch=request.user.branch,
            doctor_id=selected_doctor_id,
            clinic_id=selected_clinic_id,
            date=today,
            start_time=selected_start_time,
            end_time=selected_end_time,
            defaults={
                "total_revenue": schedule_revenue,
                "total_patients": schedule_patients_count,
            },
        )
        if schedule_stats.total_revenue != schedule_revenue or schedule_stats.total_patients != schedule_patients_count:
            schedule_stats.total_revenue = schedule_revenue
            schedule_stats.total_patients = schedule_patients_count
            schedule_stats.save()
    context = {
        "appointments": appointments,
        "today": today,
        "selected_date": selected_date_str or today.strftime("%Y-%m-%d"),
        "schedule_slots": schedule_slots,
        "selected_doctor_id": selected_doctor_id,
        "selected_clinic_id": selected_clinic_id,
        "selected_start": selected_start,
        "selected_end": selected_end,
        "selected_specialization_id": selected_specialization_id,
        "specializations": Specialization.objects.filter(deleted_date__isnull=True),
        "arrived_statuses": {"ARRIVED", "COMPLETED"},
        "day_total_revenue": day_total_revenue,
        "day_total_patients": day_total_patients,
        "schedule_revenue": schedule_revenue,
        "schedule_patients_count": schedule_patients_count,
    }
    return render(request, "appointment/today.html", context)

@login_required
@require_POST
def check_in_appointment(request):
    appointment_id = request.POST.get("id")
    if not appointment_id:
        messages.error(request, "رقم الموعد غير صالح")
        return redirect("appointments-today")

    appointment = Appointment.objects.filter(
        branch=request.user.branch,
        id=appointment_id,
        deleted_date__isnull=True,
    ).select_related("status").first()

    if not appointment:
        messages.error(request, "الموعد غير موجود")
        return redirect("appointments-today")

    arrived_status, _ = Status.objects.get_or_create(name="ARRIVED")
    appointment.status = arrived_status
    appointment.updated_by = request.user
    appointment.updated_date = get_local_now()
    appointment.save()

    messages.success(request, "تم تسجيل حضور المريض")
    return redirect("appointments-today")


@login_required
@require_POST
def quick_create_appointment(request):
    patient_id = request.POST.get("patient_id")
    patient_phone = request.POST.get("patient_phone")
    patient_name = request.POST.get("patient_name")
    doctor_id = request.POST.get("doctor_id")
    clinic_id = request.POST.get("clinic_id")
    date_str = request.POST.get("date")
    time_str = request.POST.get("time")
    status_name = request.POST.get("status", "OPEN")
    service_type = request.POST.get("service_type", "consultation")
    service_price = request.POST.get("service_price", "0")
    notes = request.POST.get("notes", "")

    if not all([doctor_id, clinic_id, date_str, time_str]):
        messages.error(request, "البيانات الأساسية مطلوبة")
        return redirect("appointments-today")

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "صيغة التاريخ غير صحيحة")
        return redirect("appointments-today")

    time_value = parse_time(time_str)
    if not time_value:
        messages.error(request, "صيغة الوقت غير صحيحة")
        return redirect("appointments-today")

    patient = None
    if patient_id:
        patient = Patient.objects.filter(branch=request.user.branch, id=patient_id).first()
    if not patient and patient_phone:
        patient = Patient.objects.filter(branch=request.user.branch, phone_number=patient_phone).first()
    if not patient and patient_phone and patient_name:
        patient = Patient.objects.create(
            name=patient_name,
            phone_number=patient_phone,
            branch=request.user.branch,
            added_by=request.user,
            added_date=get_local_now(),
            updated_by=request.user,
            updated_date=get_local_now(),
        )
    doctor = Doctor.objects.filter(branch=request.user.branch, id=doctor_id).first()
    clinic = Clinic.objects.filter(branch=request.user.branch, id=clinic_id).first()

    if not patient:
        messages.error(request, "يرجى إدخال رقم هاتف صحيح واسم المريض")
        return redirect("appointments-today")
    if not all([doctor, clinic]):
        messages.error(request, "بيانات المريض أو الطبيب أو العيادة غير صحيحة")
        return redirect("appointments-today")

    existing_appointment = Appointment.objects.filter(
        branch=request.user.branch,
        deleted_date__isnull=True,
        patient__phone_number=patient.phone_number,
        doctor=doctor,
        date=date,
    ).exists()
    if existing_appointment:
        messages.error(request, "هذا الرقم لديه موعد محجوز في نفس التاريخ")
        return redirect("appointments-today")

    status_obj, _ = Status.objects.get_or_create(name=status_name)

    try:
        service_price_value = float(service_price)
    except ValueError:
        service_price_value = 0

    Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        clinic=clinic,
        status=status_obj,
        service_type=service_type,
        service_price=service_price_value,
        date=date,
        time=time_value,
        notes=notes,
        branch=request.user.branch,
        added_by=request.user,
        added_date=get_local_now(),
        updated_by=request.user,
        updated_date=get_local_now(),
    )

    messages.success(request, "تم إنشاء موعد جديد")
    return redirect("appointments-today")
@login_required
def get_clinic_time_slots(request,clinic_id):
    clinic_slots = ClinicSlot.objects.filter(
        clinic_id = clinic_id,
        clinic__branch=request.user.branch,
        deleted_date__isnull=True
    ).values('id','start_time', 'end_time').distinct().order_by('start_time')
    
    return JsonResponse({
        'success' : True,
        'slots' : [slot for slot in clinic_slots]
    })
@login_required
def get_clinic_schedule(request,clinic_id):
    clinic_schedules = DoctorSchedule.objects.filter(
    branch=request.user.branch,
    clinic_id=clinic_id,
    deleted_date__isnull=True
)

    schedule_data = []  

    for schedule in clinic_schedules:
        if schedule.doctor.deleted_date is None:
            print(f"Schedule ID: {schedule.id}, Doctor: {schedule.doctor.full_name}")

        for slot in schedule.clinic_slot.all():
            schedule_data.append({
                **schedule.to_json(),
                "start_time": slot.start_time,
                "end_time": slot.end_time
            })

            print("Added schedule:", schedule_data[-1])  

    return JsonResponse({
        'success': True,
        'schedules': schedule_data
    })
@login_required
def new_appointment(request):
    added_by     = request.user
    added_date   = get_local_now()
    updated_date = get_local_now()
    updated_by   = request.user
    typeOfReq    = request.GET.get('type', 'new')

    if typeOfReq == 'edit':
        idOfObject      = get_id_of_object(request.GET.get('id'))
        data_to_insert  = Appointment.objects.filter(branch=request.user.branch, id=idOfObject).first()
    elif typeOfReq == 'new':
        data_to_insert = None

    # Load needed data for form
    doctors = Doctor.objects.filter(branch=request.user.branch, deleted_date__isnull=True)
    clinics = Clinic.objects.filter(branch=request.user.branch, deleted_date__isnull=True)
    all_specializations = Specialization.objects.filter(deleted_date__isnull=True)

    context = {
        'doctors'             : doctors,
        'clinics'             : clinics,
        'all_specializations' : all_specializations,
        'data_to_insert'      : data_to_insert,
        'typeOfReq'           : typeOfReq,
    }

    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        if not patient_id or not Patient.objects.filter(branch=request.user.branch, id=patient_id).exists():
            messages.error(request, 'يرجى اختيار مريض صحيح')
            return redirect('/new-appointment?new')
    

        doctor_id  = request.POST.get('doctor')
        clinic_id  = request.POST.get('clinic')
        status     = request.POST.get('status', 'OPEN')
        status_obj = Status.objects.get(name=status)
        patient_obj = Patient.objects.filter(branch=request.user.branch, id=patient_id).first()
        doctor_obj  = Doctor.objects.filter(branch=request.user.branch, id=doctor_id).first()
        clinic_obj  = Clinic.objects.filter(branch=request.user.branch, id=clinic_id).first()

        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            time = datetime.strptime(time_str, "%H:%M").time()
        except (ValueError, TypeError):
            messages.error(request, 'صيغة التاريخ أو الوقت غير صحيحة')
            return redirect('/new-appointment?new')

        notes = request.POST.get('notes', '')

        if typeOfReq == 'edit':
            appointment = Appointment.objects.filter(branch=request.user.branch, id=idOfObject).first()
            if appointment:
                appointment.patient = patient_obj
                appointment.doctor = doctor_obj
                appointment.clinic = clinic_obj
                appointment.status = status_obj
                appointment.date = date
                appointment.time = time
                appointment.notes = notes
                appointment.branch = request.user.branch
                appointment.updated_by = updated_by
                appointment.updated_date = updated_date
                appointment.save()

        else:  # new
            Appointment.objects.create(
                patient=patient_obj,
                doctor=doctor_obj,
                clinic=clinic_obj,
                status=status_obj,
                date=date,
                time=time,
                notes=notes,
                branch=request.user.branch,
                added_by=added_by,
                added_date=added_date,
                updated_by=updated_by,
                updated_date=updated_date
            )

        return HttpResponseRedirect('/')

    elif request.method == 'GET':
        return render(request, 'appointment/add.html', context)

@login_required
def new_appointment_api(request):
    cur_user = request.user
    cur_date = get_local_now()
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))  # ← هنا بنقرأ JSON
            print("Received appointment data:", data)

            # مثال: استخراج البيانات
            doctor_id   = data.get('doctor_id')
            patient_id  = data.get('patient_id')
            date        = data.get('date')
            time_range        = data.get('time')
            day         = data.get('day')
            service_type       = data.get('service_type')
            service_price       = data.get('service_price')
            appt_type   = data.get('type')
            notes       = data.get('notes', '')
            status      = data.get('status', 'OPEN')
            clinic_name = data.get('clinic')
            try : 
                # تقسيم الوقت (start, end)
                start_time, end_time = None, None
                if time_range:
                    parts = time_range.split('-')
                    if len(parts) == 2:
                        start_str = parts[0].strip()  # "10:00"
                        end_str   = parts[1].strip()  # "12:00"
                        start_time = datetime.strptime(start_str, "%I:%M %p").time()
                        end_time   = datetime.strptime(end_str, "%I:%M %p").time()
                # status_obj = Status.objects.get(name=status)
                patient_obj = Patient.objects.filter(branch=request.user.branch, id=patient_id).first()
                doctor_obj  = Doctor.objects.filter(branch=request.user.branch, id=doctor_id).first()
                clinic_obj  = Clinic.objects.filter(branch=request.user.branch, name=clinic_name).first() if clinic_name else None

                # clinic_obj  = doctor_schedule.clinic if doctor_schedule.exists() else None
            except Exception as e:
                print("Error occurred while fetching related objects:", e)
                return JsonResponse({"success": False, "message": "خطأ في البيانات"}, status=400)


            try : 

                Appointment.objects.create(
                    patient=patient_obj,
                    doctor=doctor_obj,
                    clinic=clinic_obj,
                    status_id=1,
                    date=date,
                    service_type=service_type,
                    service_price=service_price,
                    time=start_time,
                    notes=notes,
                    branch=request.user.branch,
                    added_by=cur_user,
                    added_date=cur_date,
                    updated_by=cur_user,
                    updated_date=cur_date
                )
            except Exception as e:
                print("Error occurred while fetching related objects:           222222", e)
                return JsonResponse({"success": False, "message": "خطأ في البيانات"}, status=400)

            return JsonResponse({"success": True, "message": "تم حجز الموعد بنجاح"})
        except Exception as e:
            return JsonResponse({"success": False, "message": f"خطأ في البيانات: {str(e)}"}, status=400)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

@login_required
def api_get_doctors_by_specialization(request):
    specialization_id = request.GET.get('specialization')
    print(f"-----------------{specialization_id}-----------------")

    doctors = Doctor.objects.filter(
        branch=request.user.branch,
        specialization__id=specialization_id,
        deleted_date__isnull=True
    )

    return JsonResponse({
        "success": True,
        "doctors": [
            {
                "id": doctor.id,
                "name": doctor.full_name,
                "consultation_price":doctor.consultation_price,
                "examination_price":doctor.examination_price,
            }
            for doctor in doctors
        ]
    })

@login_required
def get_doctor_schedule(request):
    doctor_id = request.GET.get("doctor_id")
    if not doctor_id:
        return JsonResponse({"success": False, "message": "Doctor ID required"}, status=400)

    today = get_local_now().date()
    print(f"Fetching schedule for doctor ID: {doctor_id} on {today} {today.weekday()}")

    schedules = DoctorSchedule.objects.filter(
        branch=request.user.branch,
        doctor_id=doctor_id,
        is_active=True,
        valid_from__lte=today,
        deleted_date__isnull=True
    ).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gte=today)
    ).order_by("day_of_week__id")

    data = []
    for sch in schedules:
        # Get all clinic slots for this schedule
        slots = sch.clinic_slot.all().order_by("start_time")
        merged_slots = merge_continuous_slots(slots)

        # Add merged slot ranges to response
        slot_data = [
            {
                "start_time": start.strftime("%I:%M %p"),
                "end_time": end.strftime("%I:%M %p"),
            }
            for start, end in merged_slots
        ]

        data.append({
            "id": sch.id,
            "clinic": sch.clinic.name,
            "day": sch.day_of_week.name,
            "day_id": sch.day_of_week.id,
            "slots": slot_data,
        })

    return JsonResponse({"success": True, "schedules": data})