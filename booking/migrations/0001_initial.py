# Generated by Django 4.1.7 on 2023-08-06 14:52

import booking.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.contrib.auth.models import Group, Permission


class Migration(migrations.Migration):

    initial = True

    dependencies = [

    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('full_name', models.CharField(blank=True, max_length=50, null=True)),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('username', models.CharField(blank=True, max_length=150, null=True, unique=True)),
                ('driving_license', models.CharField(blank=True, max_length=150, null=True)),
                ('profile', models.ImageField(blank=True, null=True, upload_to='profiles')),
                ('name', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.CreateModel(
            name='Bus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bus_number', models.CharField(max_length=150, unique=True)),
                ('number_seats', models.IntegerField(default=1)),
                ('is_available', models.BooleanField(default=True)),
                ('company_name', models.CharField(max_length=150)),
                ('name', models.CharField(default='No Name', max_length=150)),
                ('bus_model', models.CharField(max_length=100)),
                ('bus_emergency_number', models.CharField(max_length=150)),
                ('luggage_capacity', models.DecimalField(decimal_places=2, max_digits=150)),
                ('tag', models.CharField(blank=True, choices=[('BESTSELLER', 'BESTSELLER'), ('FEATURED', 'FEATURED'), ('NEW', 'NEW'), ('POPULAR', 'POPULAR'), ('SALE', 'SALE'), ('UPCOMING', 'UPCOMING'), ('LAST_MINUTE', 'LAST MINUTE'), ('DISCOUNTED', 'DISCOUNTED')], default='', max_length=50, null=True)),
                ('scale', models.CharField(blank=True, choices=[('Kilometer', 'kilometer')], default='Kilometer', max_length=50, null=True)),
                ('per_scale_charges', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
            ],
            options={
                'verbose_name': 'Bus',
                'verbose_name_plural': 'Buses',
            },
        ),
        migrations.CreateModel(
            name='BusImages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to=booking.models.bus_images_path)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bus_images', to='booking.bus')),
            ],
        ),
        migrations.CreateModel(
            name='Cities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(max_length=100)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
            ],
        ),
        migrations.CreateModel(
            name='Coupons',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('one_time_use_per_user', models.BooleanField(default=True)),
                ('minimum_amount', models.DecimalField(decimal_places=2, max_digits=50)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=50)),
            ],
            options={
                'verbose_name': 'Coupon',
                'verbose_name_plural': 'Coupons',
            },
        ),
        migrations.CreateModel(
            name='FaqsCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Insurance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('description', models.TextField()),
                ('coverage_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('premium', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_name', models.CharField(max_length=50, unique=True)),
                ('seat_limit', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=50, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('email', models.CharField(blank=True, max_length=50, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=50, null=True)),
                ('sub_total', models.DecimalField(decimal_places=2, max_digits=150)),
                ('discount', models.DecimalField(decimal_places=2, max_digits=50)),
                ('grand_total', models.DecimalField(decimal_places=2, max_digits=50)),
                ('order_status', models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'InProgress'), ('Confirmed', 'Confirmed'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')], default='Pending', max_length=50)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('coupon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.coupons')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
            },
        ),
        migrations.CreateModel(
            name='StopCharges',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stop_title', models.CharField(max_length=50, unique=True)),
                ('charge_per_minute', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scale', models.CharField(blank=True, choices=[('Kilometer', 'kilometer')], default='Kilometer', max_length=50, null=True)),
                ('per_scale_charges', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('number_passengers', models.IntegerField(default=1)),
                ('number_children', models.IntegerField(default=1)),
                ('number_adults', models.IntegerField(default=1)),
                ('is_driver_required', models.BooleanField(default=True)),
                ('is_id_verified', models.BooleanField(default=True)),
                ('weight_of_luggage', models.DecimalField(decimal_places=2, default=0, max_digits=150)),
                ('is_seat_belts_required', models.BooleanField(default=True)),
                ('is_insurance_required', models.BooleanField(default=False)),
                ('is_trailer_required', models.BooleanField(default=False)),
                ('is_collision_damage_required', models.BooleanField(default=False)),
                ('trip_status', models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'InProgress'), ('Completed', 'Completed'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')], default='Pending', max_length=50)),
                ('on_going_date', models.DateField(blank=True, null=True)),
                ('return_date', models.DateField(blank=True, null=True)),
                ('bus_returned_date', models.DateField(blank=True, null=True)),
                ('is_two_way_trip', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.bus')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Trip',
                'verbose_name_plural': 'Trips',
            },
        ),
        migrations.CreateModel(
            name='UserLicense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license', models.FileField(upload_to=booking.models.license_path)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('InProgress', 'InProgress'), ('Verified', 'Verified'), ('NotVerified', 'NotVerified')], default='Pending', max_length=30)),
                ('license_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.license')),
                ('trip', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trip_license', to='booking.trip')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TripInsurance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('insurance', models.ManyToManyField(to='booking.insurance')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trip_insurances', to='booking.trip')),
            ],
        ),
        migrations.CreateModel(
            name='Stops',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(blank=True, max_length=150, null=True)),
                ('latitude', models.CharField(blank=True, max_length=150, null=True)),
                ('longitude', models.CharField(blank=True, max_length=150, null=True)),
                ('minutes', models.IntegerField(default=10)),
                ('route_type', models.CharField(choices=[('on_going', 'On going'), ('return_back', 'Return Back')], default='on_going', max_length=50)),
                ('stop_charge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.stopcharges')),
            ],
            options={
                'verbose_name': 'Stop',
                'verbose_name_plural': 'Stops',
            },
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('route_type', models.CharField(choices=[('on_going', 'On going'), ('return_back', 'Return Back')], default='on_going', max_length=50)),
                ('departure_latitude', models.CharField(blank=True, max_length=150, null=True)),
                ('departure_longitude', models.CharField(blank=True, max_length=150, null=True)),
                ('departure_city', models.CharField(blank=True, max_length=150, null=True)),
                ('destination_latitude', models.CharField(blank=True, max_length=150, null=True)),
                ('destination_longitude', models.CharField(blank=True, max_length=150, null=True)),
                ('destination_city', models.CharField(blank=True, max_length=150, null=True)),
                ('number_of_stops', models.IntegerField(default=0)),
                ('total_distance', models.CharField(blank=True, max_length=255, null=True)),
                ('total_distance_in_km', models.CharField(blank=True, max_length=255, null=True)),
                ('estimated_time', models.CharField(max_length=20)),
                ('toll_charges', models.DecimalField(decimal_places=2, default=0, max_digits=50)),
                ('pickup_time', models.CharField(blank=True, max_length=40, null=True)),
                ('pickup_date', models.DateField(blank=True, null=True)),
                ('drop_off_time', models.CharField(blank=True, max_length=40, null=True)),
                ('drop_off_date', models.DateField(blank=True, null=True)),
                ('bus_stops', models.ManyToManyField(to='booking.stops')),
                ('trip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes', to='booking.trip')),
            ],
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('refund_amount', models.DecimalField(decimal_places=2, max_digits=150)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=50)),
                ('refund_status', models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'InProgress'), ('Paid', 'Paid'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')], default='Pending', max_length=50)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refund', to='booking.order')),
            ],
            options={
                'verbose_name': 'Refund',
                'verbose_name_plural': 'Refunds',
            },
        ),
        migrations.CreateModel(
            name='Payments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_gateway', models.CharField(blank=True, choices=[('Stripe', 'Stripe'), ('Xero', 'Xero')], max_length=50, null=True)),
                ('payment_id', models.CharField(blank=True, max_length=150, null=True)),
                ('payment_intent_id', models.CharField(blank=True, max_length=150, null=True)),
                ('payment_intent_secret', models.CharField(blank=True, max_length=150, null=True)),
                ('payment_status', models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'InProgress'), ('Paid', 'Paid'), ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')], default='Pending', max_length=50)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_payments', to='booking.order')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='trip',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order', to='booking.trip'),
        ),
        migrations.CreateModel(
            name='FeaturedTrips',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('discount_price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('rating', models.DecimalField(decimal_places=1, max_digits=2)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='busbus', to='booking.busimages')),
                ('trip_location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trip_location', to='booking.route')),
            ],
        ),
        migrations.CreateModel(
            name='Faqs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=100)),
                ('answer', models.CharField(max_length=500)),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category', to='booking.faqscategory')),
            ],
        ),
    ]
