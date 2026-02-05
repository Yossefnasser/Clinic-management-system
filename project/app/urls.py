from django.urls import path, include

from .com import auth, dashboard ,patient ,appointment,doctors,users
from rest_framework.routers import DefaultRouter

urlpatterns = [
    path('',            dashboard.dashboard, name='dashboard'),

    path('auth/login',  auth.login_view, name='login'),
    path('auth/logout', auth.logout_view, name='logout'),

    path('users/list', users.list_of_users, name='list-of-users'),
    path('users/get-list-of-users', users.get_list_of_users, name='get-list-of-users'),
    path('users/add-user', users.add_new_user, name='add-user'),
    path('users/details', users.user_details, name='user-details'),
    path('users/delete', users.delete_user, name='delete-user'),
    path('check-if-username-exists', users.check_if_username_exists, name='check-if-username-exists'),

    path('list-of-doctors', doctors.list_of_doctors, name='list-of-doctors'),
    path('get-list-of-doctors', doctors.get_list_of_doctors, name='get-list-of-doctors'),
    path('add-doctor',  doctors.add_new_doctor, name='add-doctor'),
    path('doctor-details', doctors.doctor_details, name='doctor-details'),
    
    path('delete-doctor',   doctors.delete_doctor, name='delete-doctor'),
    path('check-if-doctor-exists', doctors.check_if_doctor_exists, name='check-if-doctor-exists'),
    
    path('doctor-schedule/add/', doctors.doctor_schedule, name='add-doctor-schedule'),
    path('doctor-schedule/update/<int:schedule_id>/', doctors.doctor_schedule, name='update-doctor-schedule'),
    path('doctor-schedule/delete/<int:schedule_id>/',doctors.delete_doctor_schedule, name='delete-doctor-schedule'),
    path('api/time-slots/',doctors.api_get_slots, name='api-get-slots'),
    path('api/doctors/<int:doctor_id>/latest-appointments/', doctors.get_latest_appointments, name='get_latest_appointments'),  

    path('add-patient',              patient.add_new_patient,           name='add-patient'),
    path('list-of-patients',         patient.list_of_patient,           name='list-of-patients'),
    path('get-list-of-patients',     patient.get_list_of_patients,      name='get-list-of-patients'),
    path('delete-patient',           patient.delete_patient,            name='delete-patient'),
    path('check-if-patient-exists',  patient.check_if_patient_exists,   name='check-if-patient-exists'),
    path('add-new-patient-ajax',     patient.add_new_patient_ajax,      name='add-new-patient-ajax'),
    path('patient-details',          patient.patient_details,           name='patient-details'),
    path('api/patients/<int:patient_id>/latest-appointments/', patient.get_latest_appointments, name='get_latest_appointments'),
    
    path('add-appointment', appointment.new_appointment, name='add-appointment'),
    path('list-of-oppointments',appointment.list_of_appointments , name= 'list-of-appointments'),
    path('api/new-appointment', appointment.new_appointment_api, name='api_new_appointment'),
    path('api/clinics/<int:clinic_id>/time-slots/', appointment.get_clinic_time_slots, name='get_clinic_time_slots'),
    path('api/clinics/<int:clinic_id>/schedule/', appointment.get_clinic_schedule, name='get_clinic_schedule'),
    path('api/get-doctors-by-specialization', appointment.api_get_doctors_by_specialization, name='api_get_doctors_by_specialization'),
    path('api/get-doctor-schedule', appointment.get_doctor_schedule, name='get_doctor_schedule'),
    path('api/add-patient-ajax', patient.add_new_patient_ajax, name='add_patient_ajax'),
]
