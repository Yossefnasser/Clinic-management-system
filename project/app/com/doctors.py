from datetime import datetime
import json
from urllib import request
from django.shortcuts import render
from app.models import Appointment, Clinic, DaysOfWeek, Doctor, DoctorSchedule, Invoice, Specialization,ClinicSlot
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from app.templatetags.helpers import check_if_post_input_valid, check_valid_text, get_id_hashed_of_object, get_id_of_object , delete, merge_continuous_slots
from django.db.models import Q ,  Count, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from project.settings import CHAR_100, CHAR_50
from django.contrib.auth.decorators import login_required

@login_required
def list_of_doctors(request):
    return render(request, 'doctors/list.html')

@login_required
def get_list_of_doctors(request):
    try:
        draw            = int(request.GET.get('draw', 1))
        start           = int(request.GET.get('start', 0))
        length          = int(request.GET.get('length', 10))
        search_value    = request.GET.get('search[value]', '').strip()

        page_number = (start // length) + 1

        # Add ordering to avoid pagination warning
        queryset = Doctor.objects.filter(branch=request.user.branch, deleted_date__isnull=True).order_by('id')
        
        if search_value:
            queryset = queryset.filter(
                Q(full_name__icontains=search_value) |
                Q(phone_number__icontains=search_value) |
                Q(id__icontains=search_value)
            )

        paginator = Paginator(queryset, length)
        
        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        # Try-catch around to_json() in case that's where the Fernet error occurs
        data = []
        for doctor in page_obj:
            try:
                data.append(doctor.to_json())
            except Exception as e:
                print(f"Error serializing doctor {doctor.id}: {str(e)}")
                continue

        return JsonResponse({
            "draw": draw,
            "recordsTotal": queryset.count(),
            "recordsFiltered": queryset.count(),
            "data": data
        })

    except Exception as e:
        print(f"Error in get_list_of_doctors: {str(e)}", exc_info=True)
        return JsonResponse({
            "draw": draw if 'draw' in locals() else 0,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)  # Include error message for debugging
        }, status=500)

@login_required
def add_new_doctor(request):
    added_by     = request.user
    added_date   = datetime.now()
    updated_date = datetime.now()
    updated_by   = request.user
    typeOfReq    = request.GET.get('type', 'new')

    doctor_schedules = []

    if typeOfReq == 'edit':
        idOfObject       = get_id_of_object(request.GET.get('id'))
        data_to_insert   = Doctor.objects.filter(branch=request.user.branch, id=idOfObject).first()
        doctor_schedules = DoctorSchedule.objects.filter(
            branch=request.user.branch,
            doctor_id=idOfObject, 
            deleted_date__isnull=True
        )
        days_of_week = DaysOfWeek.objects.all()
        print(" data to insert consultation_price , examination_price ", data_to_insert.consultation_price , data_to_insert.examination_price)
        for s in doctor_schedules:
            slots = s.clinic_slot.all().order_by('start_time')
            merged = merge_continuous_slots(slots)
            s.merged_slots = [
                {"start": m[0].strftime("%I:%M %p"), "end": m[1].strftime("%I:%M %p")}
                for m in merged
            ]
    elif typeOfReq == 'new':
        data_to_insert      = None
        doctor_schedules    = None
    days_of_week = DaysOfWeek.objects.all()
    all_specializations     = Specialization.objects.filter(deleted_date__isnull=True)
    clinics                 = Clinic.objects.filter(branch=request.user.branch, deleted_date__isnull=True)
    clinic_slots      = ClinicSlot.objects.filter(clinic__branch=request.user.branch, deleted_date__isnull=True).order_by('start_time')
    
        
    context = {
        'data_to_insert'      : data_to_insert,
        'typeOfReq'           : typeOfReq,
        'all_specializations' : all_specializations,
        'clinics'             : clinics,
        'doctor_schedules'    : doctor_schedules,
        'days_of_week'        : days_of_week,
        'clinic_slots'        : clinic_slots,
    }

    if request.method == 'POST':
        full_name            = check_if_post_input_valid(request.POST['full_name'], CHAR_100)
        email                = request.POST.get('email', '').strip()
        if email:
            email = check_valid_text(email)
        else : 
            email = None

        phone_number         = check_if_post_input_valid(request.POST['phone_number'], CHAR_100)
        specialization_id    = request.POST.get('specialization')
        examination_price    = request.POST.get('examination_price', '').strip()
        consultation_price   = request.POST.get('consultation_price', '').strip()

        if examination_price  : 
            examination_price = float(examination_price)
        else : 
            examination_price = None

        if consultation_price:
            consultation_price = float(consultation_price)
        else:
            consultation_price = None

        print(" -------------------------- all data --------------------------")
        print("Full Name:", full_name)
        print("Email:", email)
        print("Phone Number:", phone_number)
        print("Specialization ID:", specialization_id)

        specialization_obj = Specialization.objects.filter(id=specialization_id).first()

        if typeOfReq == 'edit':
            doctor_obj = Doctor.objects.filter(branch=request.user.branch, id=idOfObject).first()

            doctor_obj.full_name               = full_name
            doctor_obj.phone_number            = phone_number
            doctor_obj.email                   = email
            doctor_obj.specialization          = specialization_obj
            doctor_obj.updated_by              = updated_by
            doctor_obj.updated_date            = updated_date
            doctor_obj.examination_price      = examination_price
            doctor_obj.consultation_price     = consultation_price
            doctor_obj.save()
            
            hashed_id = request.GET.get('id')

        elif typeOfReq == 'new':
            data_to_insert = Doctor.objects.create(
                full_name           = full_name,
                phone_number        = phone_number,
                email               = email,
                specialization      = specialization_obj, 
                branch              = request.user.branch,
                added_by            = added_by,
                added_date          = added_date,
                updated_by          = updated_by,
                examination_price   = examination_price,
                consultation_price  = consultation_price,
                updated_date        = updated_date
            )
            data_to_insert.save()
            hashed_id = get_id_hashed_of_object(data_to_insert.id)

        return HttpResponseRedirect('/add-doctor?type=edit&id=%s' % hashed_id)

    elif request.method == 'GET':
        return render(request, 'doctors/add.html', context)

@login_required
def delete_doctor(request):
    doctor_id      = request.POST['id']

    delete(request, Doctor, Q(branch=request.user.branch, id = doctor_id))

    allJson             = {"Result": "Fail"}
    allJson['Result']   = "Success"

    if allJson != None:
        return JsonResponse(allJson, safe=False)
    else:
        allJson['Result'] = "Fail"
        return JsonResponse(allJson, safe=False)
    

@login_required
def check_if_doctor_exists(request):
    if request.method == 'GET':
        phone_number = request.GET.get('phone_number', '').strip()
        doctor_id   = request.GET.get('id', None)

        if not phone_number:
            return JsonResponse({'exists': False})
        
        query = Doctor.objects.filter(branch=request.user.branch, phone_number=phone_number)
        if doctor_id:
            query = query.exclude(id=doctor_id)
            
        doctor = query.first()
        return JsonResponse({
            'exists': doctor is not None,
            'doctor'       : {
                'id'        : doctor.id if doctor else None,
                'name'      : doctor.name if doctor else None,
            }
        })
    return JsonResponse({'exists': False})

@login_required
def doctor_schedule(request, schedule_id=None):
    if request.method == 'POST':
        try:
            doctor_id       = request.POST.get('doctor_id')
            clinic_id       = request.POST.get('clinic')
            day_of_week_id  = request.POST.get('day_of_week')
            
            valid_from      = request.POST.get('valid_from')
            valid_to        = request.POST.get('valid_to')
            
            doctor          = Doctor.objects.filter(branch=request.user.branch, id=doctor_id).first()
            clinic          = Clinic.objects.filter(branch=request.user.branch, id=clinic_id).first()
            day_of_week     = DaysOfWeek.objects.get(id=day_of_week_id)
            
            slot_ids_str = request.POST.get('clinic_slot_ids', '[]')
            slot_ids = json.loads(slot_ids_str)
            
            clinic_slots = ClinicSlot.objects.filter(id__in=slot_ids).order_by('start_time')

            if schedule_id is not None:
                schedule = DoctorSchedule.objects.filter(branch=request.user.branch, id=schedule_id).first()
                schedule.doctor              = doctor
                schedule.clinic              = clinic
                schedule.day_of_week         = day_of_week
                schedule.valid_from          = valid_from
                schedule.valid_to            = valid_to
                schedule.branch              = request.user.branch
                schedule.save()
                message = 'Doctor schedule updated successfully.'
                schedule.clinic_slot.set(slot_ids)

            else:  
                schedule = DoctorSchedule.objects.create(
                    doctor              = doctor,
                    clinic              = clinic,
                    day_of_week         = day_of_week,
                    valid_from          = valid_from,
                    valid_to            = valid_to,
                    branch              = request.user.branch
                )
                schedule.clinic_slot.set(clinic_slots)
                message = 'Doctor schedule created successfully.'
            

            return JsonResponse({
                "success": True,
                "message": message,
                "id": schedule.id,
                "doctor": schedule.doctor.full_name,
                })
        except Exception as e:
            print(f"Error in doctor_schedule POST: {str(e)}")
            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)
    else:
        return JsonResponse({
            "success": False,
            "message": "Method not allowed"
        }, status=405)

@login_required
def doctor_details(request):
    idOfObject       = get_id_of_object(request.GET.get('id'))
    doctor = Doctor.objects.filter(branch=request.user.branch, id=idOfObject).first()

    doctor_schedules = DoctorSchedule.objects.filter(
        branch=request.user.branch,
        doctor=doctor, 
        deleted_date__isnull=True
    )

    doctor_appointments = Appointment.objects.filter(
        branch=request.user.branch,
        doctor=doctor, 
        deleted_date__isnull=True
    )

    total_patients = doctor_appointments.values("patient").distinct().count()

    invoices = Invoice.objects.filter(
        appointment__branch=request.user.branch,
        appointment__doctor=doctor,
        deleted_date__isnull=True
    )

    total_revenue = invoices.aggregate(Sum("total_price"))["total_price__sum"] or 0

    total_appointments = doctor_appointments.count()
    completed_appointments = doctor_appointments.filter(
        status__name="Completed"
    ).count()

    days_of_week = DaysOfWeek.objects.all()
    for s in doctor_schedules:
        slots = s.clinic_slot.all().order_by('start_time')
        merged = merge_continuous_slots(slots)
        s.merged_slots = [
            {"start": m[0].strftime("%I:%M %p"), "end": m[1].strftime("%I:%M %p")}
            for m in merged
        ]
    context = {
        "doctor": doctor,
        "doctor_schedules": doctor_schedules,
        "doctor_appointments": doctor_appointments,
        "days_of_week": days_of_week,
        # stats
        "total_patients": total_patients,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "completed_appointments": completed_appointments,
    }
    return render(request, "doctors/details.html", context)

@login_required
def delete_doctor_schedule(request,schedule_id):
    try:
        delete(request, DoctorSchedule, Q(id = schedule_id))
        return JsonResponse({
            'success' : True, 
        })
    except Exception as e :
        return JsonResponse({
            'success' : True, 
            'message' : str(e)
        },status=500)

@login_required
def api_get_slots(request):
    clinic_id       = request.GET.get('clinic_id')
    day_of_week_id  = request.GET.get('day_of_week_id')

    clinic_slots = ClinicSlot.objects.filter(
        clinic_id=clinic_id,
        is_active=True,
        deleted_date__isnull=True
    )

    slots_data = []
    for slot in clinic_slots:
        # Check if slot is occupied by any doctor
        doctor_schedule = DoctorSchedule.objects.filter(
            branch=request.user.branch,
            clinic_slot=slot,
            day_of_week_id = day_of_week_id,
            is_active=True,
            deleted_date__isnull=True
        ).first()
        
        slot_json = slot.to_json()
        if doctor_schedule and doctor_schedule.doctor.deleted_date is None:
            slot_json['is_available'] = False
            slot_json['doctor_name'] = doctor_schedule.doctor.full_name 
        else:
            slot_json['is_available'] = True
            slot_json['doctor_name'] = None
        
        slots_data.append(slot_json)
    
    return JsonResponse({
        "success": True,
        "slots": slots_data
    })

@login_required
def get_latest_appointments(request, doctor_id):
    try:
        doctor = Doctor.objects.filter(branch=request.user.branch, id=doctor_id, deleted_date__isnull=True).first()
        latest_appointments = Appointment.objects.filter(
            branch=request.user.branch,
            doctor=doctor,
            deleted_date__isnull=True
        ).order_by('-date')
        appointment_data = [appt.tojson()for appt in latest_appointments]
        return JsonResponse({
            'success': True,
            'appointments': appointment_data
        })
    except Doctor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Doctor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)