from datetime import datetime

from django.utils import timezone


def get_local_now():
	return timezone.localtime()


def get_local_date():
	return timezone.localtime().date()


def get_local_time():
	return timezone.localtime().time()


def parse_time(value):
	if not value:
		return None
	for fmt in ("%H:%M", "%I:%M %p"):
		try:
			return datetime.strptime(value, fmt).time()
		except ValueError:
			continue
	return None


def get_doctor_branch_profile(doctor, branch):
	if not doctor or not branch:
		return None
	from app.models import DoctorBranch
	return DoctorBranch.objects.filter(
		doctor=doctor,
		branch=branch,
		deleted_date__isnull=True,
		is_active=True,
	).first()


def apply_doctor_branch_pricing(doctor, branch):
	profile = get_doctor_branch_profile(doctor, branch)
	if profile:
		doctor.global_consultation_price = getattr(doctor, 'consultation_price', None)
		doctor.global_examination_price = getattr(doctor, 'examination_price', None)
		doctor.consultation_price = profile.consultation_price
		doctor.examination_price = profile.examination_price
		doctor.branch_profile = profile
	else:
		doctor.global_consultation_price = getattr(doctor, 'consultation_price', None)
		doctor.global_examination_price = getattr(doctor, 'examination_price', None)
		doctor.branch_profile = None
	return doctor
