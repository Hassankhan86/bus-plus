# Generated by Django 4.1.7 on 2023-08-15 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_alter_busimages_options_alter_cities_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='insurance',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
