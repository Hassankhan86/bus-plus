# Generated by Django 4.1.7 on 2023-09-09 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0020_remove_trip_is_two_way_trip_trip_trip_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='self_drive_available',
            field=models.BooleanField(default=False),
        ),
    ]
