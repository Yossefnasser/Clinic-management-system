from datetime import datetime
from django.shortcuts import render
from app.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from app.templatetags.helpers import check_if_post_input_valid, check_valid_text, get_id_hashed_of_object, get_id_of_object, delete
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from project.settings import CHAR_100, CHAR_50
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required

@login_required
def list_of_users(request):
    return render(request, 'users/list.html')

@login_required
def get_list_of_users(request):
    try:
        draw            = int(request.GET.get('draw', 1))
        start           = int(request.GET.get('start', 0))
        length          = int(request.GET.get('length', 10))
        search_value    = request.GET.get('search[value]', '').strip()

        page_number = (start // length) + 1

        # Filter active users only (not deleted)
        queryset = User.objects.filter(branch=request.user.branch, is_active=True).order_by('id')
        
        if search_value:
            queryset = queryset.filter(
                Q(fullname__icontains=search_value) |
                Q(username__icontains=search_value) |
                Q(phone_number__icontains=search_value) |
                Q(id__icontains=search_value)
            )

        paginator = Paginator(queryset, length)
        
        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        data = []
        for user in page_obj:
            try:
                data.append({
                    'id': user.id,
                    'hash_id': get_id_hashed_of_object(user.id),
                    'fullname': user.fullname or user.username,
                    'username': user.username,
                    'user_type': user.user_type,
                    'phone_number': user.phone_number or '',
                    'is_active': user.is_active
                })
            except Exception as e:
                print(f"Error serializing user {user.id}: {str(e)}")
                continue

        return JsonResponse({
            "draw": draw,
            "recordsTotal": queryset.count(),
            "recordsFiltered": queryset.count(),
            "data": data
        })

    except Exception as e:
        print(f"Error in get_list_of_users: {str(e)}", exc_info=True)
        return JsonResponse({
            "draw": draw if 'draw' in locals() else 0,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": str(e)
        }, status=500)

@login_required
def add_new_user(request):
    typeOfReq = request.GET.get('type', 'new')

    if typeOfReq == 'edit':
        idOfObject = get_id_of_object(request.GET.get('id'))
        data_to_insert = User.objects.filter(branch=request.user.branch, id=idOfObject).first()
    elif typeOfReq == 'new':
        data_to_insert = None

    context = {
        'data_to_insert': data_to_insert,
        'typeOfReq': typeOfReq,
        'user_types': User.UserType.choices,
    }

    if request.method == 'POST':
        fullname = check_if_post_input_valid(request.POST['fullname'], CHAR_100)
        username = check_if_post_input_valid(request.POST['username'], CHAR_50)
        phone_number = check_if_post_input_valid(request.POST.get('phone_number', ''), CHAR_100)
        user_type = request.POST.get('user_type')
        is_active = request.POST.get('is_active') == 'on'
        password = request.POST.get('password', '').strip()

        if typeOfReq == 'edit':
            user_obj = User.objects.filter(branch=request.user.branch, id=idOfObject).first()
            
            user_obj.fullname = fullname
            user_obj.username = username
            user_obj.phone_number = phone_number
            user_obj.user_type = user_type
            user_obj.is_active = is_active
            
            # Only update password if provided
            if password:
                user_obj.password = make_password(password)
            
            user_obj.save()
            hashed_id = request.GET.get('id')

        elif typeOfReq == 'new':
            # Password is required for new users
            if not password:
                messages.error(request, 'كلمة المرور مطلوبة للمستخدم الجديد')
                return render(request, 'users/add.html', context)
            
            data_to_insert = User.objects.create(
                fullname=fullname,
                username=username,
                phone_number=phone_number,
                user_type=user_type,
                is_active=is_active,
                branch=request.user.branch,
                password=make_password(password)
            )
            data_to_insert.save()
            hashed_id = get_id_hashed_of_object(data_to_insert.id)

        return HttpResponseRedirect('/users/add-user?type=edit&id=%s' % hashed_id)

    elif request.method == 'GET':
        return render(request, 'users/add.html', context)

@login_required
def delete_user(request):
    user_id = request.POST['id']
    
    # Soft delete by setting is_active to False instead of actual deletion
    user = User.objects.filter(branch=request.user.branch, id=user_id).first()
    if user:
        user.is_active = False
        user.save()
    
    allJson = {"Result": "Success"}
    return JsonResponse(allJson, safe=False)

@login_required
def user_details(request):
    idOfObject = get_id_of_object(request.GET.get('id'))
    user = User.objects.filter(branch=request.user.branch, id=idOfObject).first()

    context = {
        "user": user,
    }
    return render(request, "users/details.html", context)

@login_required
def check_if_username_exists(request):
    if request.method == 'GET':
        username = request.GET.get('username', '').strip()
        user_id = request.GET.get('id', None)

        if not username:
            return JsonResponse({'exists': False})
        
        query = User.objects.filter(branch=request.user.branch, username=username)
        if user_id:
            query = query.exclude(id=user_id)
            
        user = query.first()
        return JsonResponse({
            'exists': user is not None,
            'user': {
                'id': user.id if user else None,
                'fullname': user.fullname if user else None,
            }
        })
    return JsonResponse({'exists': False})
