import datetime
import time
from django.db import models  
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from django.utils import timezone

from app.templatetags.helpers import get_id_hashed_of_object


class Branch(models.Model):
    """Clinic branch model"""
    address     = models.TextField()
    phone_number= models.CharField(max_length=15, blank=True, null=True)
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.address}"

class User(AbstractUser):
    class UserType(models.TextChoices):
        MANAGER   = 'MANAGER', 'Manager'
        ADMIN     = 'ADMIN', 'Admin'
        SECRETARY = 'SECRETARY', 'Secretary'

    # Keep username for login
    fullname  = models.CharField(max_length=100, null=True, blank=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.SECRETARY,
        null=True
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    branch    = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    REQUIRED_FIELDS = ['fullname']  # for createsuperuser

    def __str__(self):
        return f"{self.fullname or self.username} ({self.get_user_type_display()})"

class BaseModel(models.Model):
    added_date   = models.DateTimeField(default=timezone.now, null=True, blank=True)
    deleted_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    added_by     = models.ForeignKey(User, on_delete=models.PROTECT, related_name='%(class)s_added_by', null=True, blank=True)
    deleted_by   = models.ForeignKey(User, on_delete=models.PROTECT, related_name='%(class)s_deleted_by', null=True, blank=True)
    updated_by   = models.ForeignKey(User, on_delete=models.PROTECT, related_name='%(class)s_updated_by', null=True, blank=True)

    class Meta:
        abstract = True

class Specialization(BaseModel):
    """Specialization model"""
    name = models.CharField(max_length=100, unique=True)

    def to_json(self):
        return {
            'id'        : self.id,
            'hash_id'   : get_id_hashed_of_object(self.id),
            'name'      : self.name,
        }

    def __str__(self):
        return self.name
    
class Doctor(BaseModel):
    """Doctor information model"""
    full_name                = models.CharField(max_length=100)
    specialization           = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name="doctors")
    phone_number             = models.CharField(max_length=15, blank=True, null=True)
    email                    = models.EmailField( blank=True, null=True)
    examination_price        = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    consultation_price       = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active                = models.BooleanField(default=True)
    branch                  = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        unique_together = [['phone_number', 'branch']]
    
    def to_json(self):
        return {
            'id'            : self.id,
            'hash_id'       : get_id_hashed_of_object(self.id),
            'name'          : self.full_name,
            'phone_number'  : self.phone_number,
            'email'         : self.email,
            'specialization': self.specialization.to_json()
        }
    
    def __str__(self):
        return f"{self.full_name}"
    

class Patient(BaseModel):
    """Patient information model"""
    name            = models.CharField(max_length=100)
    phone_number         = models.CharField(max_length=15)
    age                  = models.PositiveIntegerField(null=True, blank=True , default=None)
    gender               = models.CharField(max_length=10, choices=[
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ], blank=True, null=True)
    notes                = models.TextField(blank=True, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        db_table = "Patient"
        unique_together = [['phone_number', 'branch']]

    def to_json(self):
        return {
            'id'        : self.id,
            'hash_id'   : get_id_hashed_of_object(self.id),
            'name' : self.name,
            'phone_number': self.phone_number,
            'age'       : self.age,
            'gender'    : self.gender,
            'notes'     : self.notes,
        }
    
    def __str__(self):
        return f"{self.name}"


class Clinic(BaseModel):
    """Medical departments/clinics"""
    name            = models.CharField(max_length=50)
    default_open_time = models.TimeField(default=datetime.time(13, 0))
    default_close_time = models.TimeField(default=datetime.time(23, 0))
    slot_duration_hours = models.IntegerField(default=1)
    is_active       = models.BooleanField(default=True)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    def __str__(self):
        return  f'{self.name} ({self.default_open_time} - {self.default_close_time})'

class DaysOfWeek(BaseModel):
    """Days of the week"""
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class ClinicSlot(BaseModel):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['start_time']
    def __str__(self):
        return f"{self.clinic.name} Slot ({self.start_time}-{self.end_time})"
    def clean(self):
        if self.start_time >= self.end_time :
            return ValidationError('Start time must be before end time. ')
        clinic_hours = self.clinic
        if not (clinic_hours.default_open_time <= self.start_time < self.end_time <= clinic_hours.default_close_time):
            raise ValidationError(f"Clinic slot must be within clinic hours: {clinic_hours.default_open_time} - {clinic_hours.default_close_time}.")
    def to_json(self, is_available=True, doctor_name=None):
        return {
            'id': self.id,
            'hash_id': get_id_hashed_of_object(self.id),
            'clinic': self.clinic.name,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'is_available': is_available,
            'doctor_name': doctor_name,
        }

class Status(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class DoctorSchedule(BaseModel):
    """Doctor availability schedule"""
    doctor                 = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    clinic                 = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    day_of_week            = models.ForeignKey(DaysOfWeek, on_delete=models.CASCADE)
    clinic_slot            = models.ManyToManyField(ClinicSlot)
    valid_from             = models.DateField(default=datetime.date.today)
    valid_to               = models.DateField(null=True, blank=True)
    is_active              = models.BooleanField(default=True)
    branch                 = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    
    class Meta:
        ordering = ['day_of_week']
    
    def to_json(self):
        return {
            'id'        : self.id,
            'hash_id'   : get_id_hashed_of_object(self.id),
            'clinic' : self.clinic.name,
            'doctor': self.doctor.full_name,
            'specialization' : self.doctor.specialization.pk,
            'specialization_name' :  self.doctor.specialization.name,
            'day_of_week'       : self.day_of_week.name,
            'valid_from'     : self.valid_from,
            'valid_to'     : self.valid_to,
            'is_active'     : self.is_active,
        }
    
    def clean(self):
        if self.valid_to and self.valid_from > self.valid_to:
            raise ValidationError('valid_from must be before valid_to.')
    def save(self, *args, **kwargs):
        self.full_clean()  # calls clean_fields(), clean(), and validate_unique()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.doctor} at {self.clinic} on {self.day_of_week} ({self.clinic_slot}-)"


class Appointment(BaseModel):
    """Patient appointment records"""
    
    patient  = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor   = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    clinic   = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    status   = models.ForeignKey(Status, on_delete=models.CASCADE)
    service_type    = models.CharField(max_length=20)
    service_price   = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    date     = models.DateField()
    time     = models.TimeField()
    notes    = models.TextField(blank=True, null=True)
    branch   = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.patient} with {self.doctor} at {self.time} on {self.date}"
    def tojson(self):
        return {
            'id'        : self.id,
            'hash_id'   : get_id_hashed_of_object(self.id),
            'patient'   : self.patient.to_json(),
            'doctor'    : self.doctor.to_json(),
            'clinic'    : self.clinic.name,
            'status'    : self.status.name,
            'date'      : self.date,
            'time'      : self.time.strftime('%H:%M'),
            'service_type'      : self.service_type,
            'service_price'     : self.service_price,
            'notes'     : self.notes,
        }

class Invoice(BaseModel):
    """Clinic invoices"""
    
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    paid_before = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status      = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='invoices')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Generate invoice number that resets daily"""
        if not self.pk:  # Only on creation
            today_invoices = Invoice.objects.filter(
                created_at__date=self.created_at.date()
            ).count()
            self.invoice_number = today_invoices + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.invoice_number} for {self.appointment.patient}"