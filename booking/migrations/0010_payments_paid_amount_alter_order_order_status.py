# Generated by Django 4.1.7 on 2023-08-24 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_alter_payments_payment_gateway_alter_trip_bus'),
    ]

    operations = [
        migrations.AddField(
            model_name='payments',
            name='paid_amount',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('InProgress', 'InProgress'), ('Confirmed', 'Confirmed'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled'), ('Completed', 'Completed')], default='Pending', max_length=50),
        ),
    ]
