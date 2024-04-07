# Generated by Django 4.1.7 on 2023-08-27 10:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0016_contactus_alter_trip_is_driver_required_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='featuredtrips',
            name='trip_location',
        ),
        migrations.AddField(
            model_name='featuredtrips',
            name='trip',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.trip'),
        ),
        migrations.AlterField(
            model_name='featuredtrips',
            name='bus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bus_featured_trips', to='booking.bus'),
        ),
    ]