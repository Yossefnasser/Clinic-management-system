from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_printjob'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='ticket_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
