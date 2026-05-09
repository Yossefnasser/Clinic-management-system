from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def forwards(apps, schema_editor):
    Branch = apps.get_model('app', 'Branch')
    Doctor = apps.get_model('app', 'Doctor')
    DoctorBranch = apps.get_model('app', 'DoctorBranch')

    branch1 = Branch.objects.filter(pk=1).first()
    if branch1 is None:
        branch1 = Branch.objects.create(id=1, address='Default Branch', is_active=True)

    for doctor in Doctor.objects.all():
        doctor_branch = doctor.branch_id or branch1.id

        if doctor.branch_id is None:
            doctor.branch_id = branch1.id
            doctor.save(update_fields=['branch'])

        DoctorBranch.objects.update_or_create(
            doctor_id=doctor.id,
            branch_id=doctor_branch,
            defaults={
                'consultation_price': doctor.consultation_price or 0,
                'examination_price': doctor.examination_price or 0,
                'is_active': True,
            },
        )

    Doctor.objects.all().update(is_active=True)
    DoctorBranch.objects.all().update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_daily_and_schedule_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorBranch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_date', models.DateTimeField(blank=True, default=timezone.now, null=True)),
                ('deleted_date', models.DateTimeField(blank=True, null=True)),
                ('updated_date', models.DateTimeField(blank=True, default=timezone.now, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('examination_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('consultation_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_added_by', to='app.user')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='doctor_profiles', to='app.branch')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_deleted_by', to='app.user')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branch_profiles', to='app.doctor')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_updated_by', to='app.user')),
            ],
            options={
                'unique_together': {('doctor', 'branch')},
            },
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
