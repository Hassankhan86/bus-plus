# Generated by Django 4.1.7 on 2023-08-19 17:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_alter_order_order_status_alter_route_bus_stops'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payments',
            name='payment_gateway',
            field=models.CharField(blank=True, choices=[('Stripe', 'Stripe'), ('Cash', 'Cash')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='trip',
            name='bus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.bus'),
        ),
    ]