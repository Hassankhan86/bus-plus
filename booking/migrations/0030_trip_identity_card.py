# Generated by Django 4.1.7 on 2023-10-07 06:19

import booking.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0029_xero_account_name_xero_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='identity_card',
            field=models.FileField(null=True, upload_to=booking.models.trip_path),
        ),
    ]
