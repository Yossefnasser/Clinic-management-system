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
