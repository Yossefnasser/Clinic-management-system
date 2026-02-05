from datetime import datetime
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from app.templatetags.helpers import check_if_post_input_valid, check_valid_text, get_id_of_object , delete
from app.models import Doctor, Patient, Specialization, Appointment
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from project.settings import CHAR_100
from django.contrib.auth.decorators import login_required
####################  Patient  #################

@login_required
def list_of_patient(request):
    
    total_patients_count = Patient.objects.filter(branch=request.user.branch, deleted_date__isnull=True).count()
    context = {
        'total_patients_count': total_patients_count
    }
    return render(request,'patient/list.html',context)

@login_required
def get_list_of_patients(request):
    try:
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '').strip()

        page_number = (start // length) + 1

        # Add ordering to avoid pagination warning
        queryset = Patient.objects.filter(branch=request.user.branch, deleted_date__isnull=True).order_by('id')
        
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
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
        for patient in page_obj:
            try:
                data.append(patient.to_json())
            except Exception as e:
                print(f"Error serializing patient {patient.id}: {str(e)}")
                continue

        return JsonResponse({
            "draw": draw,
            "recordsTotal": queryset.count(),
            "recordsFiltered": queryset.count(),
            "data": data
        })

    except Exception as e:
        print(f"Error in get_list_of_patients: {str(e)}", exc_info=True)
        return JsonResponse({
            "draw": draw if 'draw' in locals() else 0,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)  # Include error message for debugging
        }, status=500)
    
@login_required
def add_new_patient(request):
    
    added_by     = request.user
    added_date   = datetime.now()
    updated_date = datetime.now()
    updated_by   = request.user
    typeOfReq    = request.GET.get('type', 'new')

    if typeOfReq == 'edit':
        idOfObject      = get_id_of_object(request.GET.get('id'))
        data_to_insert  = Patient.objects.filter(branch=request.user.branch, id=idOfObject).first()
    elif typeOfReq == 'new':
        data_to_insert = None

    all_specializations = Specialization.objects.filter(deleted_date__isnull=True)
    all_doctors         = Doctor.objects.filter(branch=request.user.branch, deleted_date__isnull=True)

    context = {
        'all_specializations'   : all_specializations , 
        'all_doctors'           : all_doctors , 
        'data_to_insert'        : data_to_insert,
        'typeOfReq'             : typeOfReq,
    }

    if request.method == 'POST':
        name            = check_if_post_input_valid(request.POST['name'], CHAR_100)
        phone_number         = check_if_post_input_valid(request.POST['phone'], CHAR_100)
        if typeOfReq == 'edit':
            if Patient.objects.filter(branch=request.user.branch, phone_number=phone_number).exclude(id=idOfObject).exists():
                messages.error(request, 'هذا الرقم مسجل مسبقاً لمريض آخر')
                return redirect('/add-patient?new')
        else:
            if Patient.objects.filter(branch=request.user.branch, phone_number=phone_number).exists():
                messages.error(request, 'هذا الرقم مسجل مسبقاً لمريض آخر')
                return redirect('/add-patient?new')
            
        notes                = check_valid_text(request.POST['notes'])
        age_str              = request.POST.get('age', '').strip()
        age                  = int(age_str) if age_str.isdigit() else None
        gender               = request.POST['gender'] if 'gender' in request.POST else None

        print(" ------------------------------------    data   ----------------------------" , name , phone_number ,  notes ,  age  , gender)


        if typeOfReq == 'edit':
            patient_obj = Patient.objects.filter(branch=request.user.branch, id=idOfObject).first()
            print(" ------------------------------------    patient_obj   ----------------------------" , patient_obj)

            patient_obj.name    = name
            patient_obj.phone_number = phone_number
            patient_obj.notes        = notes
            patient_obj.age          = age
            patient_obj.gender       = gender
            patient_obj.updated_by   = updated_by
            patient_obj.updated_date = updated_date
            patient_obj.save()

        elif typeOfReq == 'new':
            data_to_insert =  Patient.objects.create(
                name    = name,
                phone_number = phone_number,
                notes        = notes,
                age          = age , 
                branch       = request.user.branch,
                gender       = gender ,
                added_by     = added_by,
                added_date   = added_date,
                updated_by   = updated_by,
                updated_date = updated_date
            )
            data_to_insert.save()

        return HttpResponseRedirect('/')

    elif request.method == 'GET':
        return render(request, 'patient/add.html', context)

@login_required
def patient_details(request):
    idOfObject      = get_id_of_object(request.GET.get('id'))
    patient         = Patient.objects.filter(branch=request.user.branch, id=idOfObject).first()

    if not patient:
        messages.error(request, 'المريض غير موجود أو تم حذفه.')
        return redirect('list-of-patients')

    context = {
        'patient' : patient
    }
    return render(request, 'patient/details.html', context)

@login_required
def delete_patient(request):
    patient_id      = request.POST['id']
    delete(request, Patient, Q(branch=request.user.branch, id = patient_id))
    appointments = Appointment.objects.filter(branch=request.user.branch, patient_id=patient_id, deleted_date__isnull=True)
    delete(request, Appointment, Q(id__in = appointments.values_list('id', flat=True)))
    allJson             = {"Result": "Fail"}
    allJson['Result']   = "Success"

    if allJson != None:
        return JsonResponse(allJson, safe=False)
    else:
        allJson['Result'] = "Fail"
        return JsonResponse(allJson, safe=False)
    
@login_required
def add_new_patient_ajax(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        phone   = request.POST.get('phone', '').strip()
        age     = request.POST.get('age', '').strip()
        gender  = request.POST.get('gender', '').strip()
        notes   = request.POST.get('notes', '').strip()


        if not all([name, phone, gender]):
            return JsonResponse({'success': False, 'errors': 'Name, phone, and gender are required.'}, status=400)

        if age:
            try:
                age = int(age)
            except ValueError:
                return JsonResponse({'success': False, 'errors': 'Invalid age.'}, status=400)
        else:
            age = None


        if Patient.objects.filter(branch=request.user.branch, phone_number=phone).exists():
            return JsonResponse({'success': False, 'errors': 'This phone number is already registered.'}, status=400)


        patient = Patient.objects.create(
            name         = name,
            phone_number = phone,
            age          = age,
            gender       = gender,
            notes        = notes,
            branch       = request.user.branch,
            added_by     = request.user if request.user.is_authenticated else None,
            added_date   = timezone.now(),
            updated_by   = request.user if request.user.is_authenticated else None,
            updated_date = timezone.now()
        )

        return JsonResponse({
            'success'       : True,
            'patient_id'        : patient.id,
            'message'       : 'Patient created successfully'
        })

    return JsonResponse({'success': False, 'errors': 'Invalid request method'}, status=405)

@login_required
def check_if_patient_exists(request):
    if request.method == 'GET':
        phone_number = request.GET.get('phone_number', '').strip()
        patient_id = request.GET.get('id', None)
        
        if not phone_number:
            return JsonResponse({'exists': False})
        
        query = Patient.objects.filter(branch=request.user.branch, phone_number=phone_number , deleted_date__isnull=True)
        if patient_id:
            query = query.exclude(id=patient_id)
            
        patient = query.first()
        return JsonResponse({
            'exists': patient is not None,
            'patient'       : {
                'id'        : patient.id if patient else None,
                'name'      : patient.name if patient else None,
                'age'       : patient.age if patient else None,
                'gender'    : patient.get_gender_display() if patient else None,
                'phone'     : patient.phone_number if patient else None
            }
        })
    return JsonResponse({'exists': False})

@login_required
def get_latest_appointments(request, patient_id):
    try:
        patient = Patient.objects.get(branch=request.user.branch, id=patient_id, deleted_date__isnull=True)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    appointments = Appointment.objects.filter(branch=request.user.branch, patient=patient).order_by('-date')
    data = [appointment.tojson() for appointment in appointments]
    print(data)
    return JsonResponse({
        'success': True,
        'appointments': data
        })
