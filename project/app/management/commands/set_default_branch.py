from django.core.management.base import BaseCommand
from app.models import DoctorSchedule, Appointment, Branch, Doctor, Patient, Clinic, User


class Command(BaseCommand):
    help = 'Set branch_id=1 for all existing records that have a branch field'

    def handle(self, *args, **options):
        # Check if branch with id=1 exists
        try:
            branch = Branch.objects.get(id=1)
            self.stdout.write(self.style.SUCCESS(f'Found branch: {branch}'))
        except Branch.DoesNotExist:
            self.stdout.write(self.style.ERROR('Branch with id=1 does not exist. Please create it first.'))
            return

        # Update Doctor records
        doctors_updated = Doctor.objects.filter(branch__isnull=True).update(branch_id=1)
        self.stdout.write(self.style.SUCCESS(f'Updated {doctors_updated} Doctor records with branch_id=1'))

        # Update Patient records
        patients_updated = Patient.objects.filter(branch__isnull=True).update(branch_id=1)
        self.stdout.write(self.style.SUCCESS(f'Updated {patients_updated} Patient records with branch_id=1'))

        # Update Clinic records
        clinics_updated = Clinic.objects.filter(branch__isnull=True).update(branch_id=1)
        self.stdout.write(self.style.SUCCESS(f'Updated {clinics_updated} Clinic records with branch_id=1'))

        # Update User records
        users_updated = User.objects.filter(branch__isnull=True).update(branch_id=1)
        self.stdout.write(self.style.SUCCESS(f'Updated {users_updated} User records with branch_id=1'))

        # Update DoctorSchedule records
        schedules_updated = DoctorSchedule.objects.filter(branch__isnull=True).update(branch_id=1)
        self.stdout.write(self.style.SUCCESS(f'Updated {schedules_updated} DoctorSchedule records with branch_id=1'))

        # Update Appointment records
        appointments_updated = Appointment.objects.filter(branch__isnull=True).update(branch_id=1)
        self.stdout.write(self.style.SUCCESS(f'Updated {appointments_updated} Appointment records with branch_id=1'))

        self.stdout.write(self.style.SUCCESS('Done!'))
