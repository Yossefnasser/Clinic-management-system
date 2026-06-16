from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from app.models import Clinic, ClinicSlot, Branch


class Command(BaseCommand):
    help = "Add clinics عيادة 1 through عيادة 8 to branch 2 with 1-hour slots"

    def handle(self, *args, **options):
        try:
            branch = Branch.objects.get(id=2)
        except Branch.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Branch 2 not found"))
            return

        self.stdout.write(self.style.SUCCESS(f"✅ Found Branch: {branch.address}"))

        # Create/Update clinics عيادة 1 to عيادة 8
        clinic_names = [f"عيادة {i}" for i in range(1, 9)]
        
        for clinic_name in clinic_names:
            # Get or create clinic
            clinic, created = Clinic.objects.get_or_create(
                name=clinic_name,
                branch=branch,
                defaults={
                    "default_open_time": datetime.strptime("09:00", "%H:%M").time(),
                    "default_close_time": datetime.strptime("23:00", "%H:%M").time(),
                    "slot_duration_hours": 1,
                    "is_active": True,
                    "added_by": None,
                    "added_date": None,
                    "updated_by": None,
                    "updated_date": None,
                }
            )
            
            if not created:
                self.stdout.write(self.style.WARNING(f"⚠️  {clinic_name} already exists, adding missing morning slots..."))
            
            # Generate 1-hour slots from 09:00 to 13:00 (morning slots)
            open_time = datetime.combine(datetime.today(), datetime.strptime("09:00", "%H:%M").time())
            close_time = datetime.combine(datetime.today(), datetime.strptime("13:00", "%H:%M").time())
            slot_duration = timedelta(hours=1)
            
            created_slots = 0
            while open_time + slot_duration <= close_time:
                # Check if slot already exists
                if not ClinicSlot.objects.filter(
                    clinic=clinic,
                    start_time=open_time.time(),
                    end_time=(open_time + slot_duration).time()
                ).exists():
                    ClinicSlot.objects.create(
                        clinic=clinic,
                        start_time=open_time.time(),
                        end_time=(open_time + slot_duration).time(),
                        is_active=True,
                        added_by=None,
                        added_date=None,
                        updated_by=None,
                        updated_date=None,
                    )
                    created_slots += 1
                open_time += slot_duration

            # Add late slot from 23:00 to 00:00
            late_start = datetime.strptime("23:00", "%H:%M").time()
            late_end = datetime.strptime("00:00", "%H:%M").time()
            if not ClinicSlot.objects.filter(
                clinic=clinic,
                start_time=late_start,
                end_time=late_end,
            ).exists():
                ClinicSlot.objects.create(
                    clinic=clinic,
                    start_time=late_start,
                    end_time=late_end,
                    is_active=True,
                    added_by=None,
                    added_date=None,
                    updated_by=None,
                    updated_date=None,
                )
                created_slots += 1
            
            status = "✅ Updated" if not created else "✅ Created"
            self.stdout.write(self.style.SUCCESS(f"{status} {clinic_name}, added {created_slots} morning slots (09:00-13:00)"))

        self.stdout.write(self.style.SUCCESS("🎯 All clinics added to Branch 2 successfully!"))
