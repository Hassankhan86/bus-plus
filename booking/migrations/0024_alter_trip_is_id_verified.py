# Generated by Django 4.1.7 on 2023-09-17 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0023_alter_buscharges_bus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='is_id_verified',
            field=models.BooleanField(default=True),
        ),
    ]