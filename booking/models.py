import math
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

from booking.api.xero import XeroClient
from booking.managers import CustomUserManager
from booking.CONSTANT import *
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, FloatField, F
from django.db.models.functions import Cast
from django.db.models import Count
from django.conf import settings

from booking.utils import parse_str_date_time


def profile_path(instance, filename):
    return "Profiles/{0}/{1}".format(instance.email, filename)


def license_path(instance, filename):
    return "License/{0}/{1}".format(instance.user.email, filename)


def trip_path(instance, filename):
    return "Trips/tripe-{0}/{1}".format(instance.id, filename)


def bus_images_path(instance, filename):
    return "Buses/{0}/{1}".format(instance.bus.bus_number, filename)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    full_name = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    driving_license = models.CharField(max_length=150, null=True, blank=True)
    profile = models.ImageField(upload_to="profiles", null=True, blank=True)
    name = models.CharField(max_length=255)
    is_order_user = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def get_profile(self):
        if self.profile:
            return self.profile
        else:
            return "defaults/no-profile.png"

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


class Bus(models.Model):
    bus_number = models.CharField(max_length=150, unique=True)
    number_seats = models.IntegerField(default=1)
    is_available = models.BooleanField(default=True)
    company_name = models.CharField(max_length=150)
    name = models.CharField(max_length=150, default="No Name")
    bus_model = models.CharField(max_length=100)
    self_drive_available = models.BooleanField(default=False)
    # current_bus_location = models.ForeignKey("Cities", null=True, blank=True)
    bus_emergency_number = models.CharField(max_length=150)
    luggage_capacity = models.DecimalField(max_digits=150, decimal_places=2)
    bus_status = models.CharField(max_length=50, choices=BUS_STATUS, default=BUS_STATUS[0][0], null=True, blank=True)
    tag = models.CharField(max_length=50, choices=BUS_TAGS, default="", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.bus_model

    def average_rating(self):
        return "5/5"

    def bus_logo(self):
        logo = self.bus_images.first()
        if not logo:
            logo = "defaults/no-image.png"
        else:
            logo = logo.image
        return logo

    class Meta:
        verbose_name = _('Bus')
        verbose_name_plural = _('Buses')


class BusCharges(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="bus_charges")
    scale = models.CharField(max_length=50, choices=BUS_CHARGES_SCALE, default=BUS_CHARGES_SCALE[0][0], null=True,
                             blank=True)
    per_scale_charges = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    class Meta:
        unique_together = ('bus', 'scale',)

    def __str__(self):
        return f"{self.bus.name} {self.scale}"


class BusImages(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="bus_images")
    image = models.ImageField(upload_to=bus_images_path, null=True, blank=True)

    class Meta:
        verbose_name = _('Bus Images')
        verbose_name_plural = _('Bus Images')


class StopCharges(models.Model):  #
    stop_title = models.CharField(max_length=50, unique=True)
    charge_per_minute = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.stop_title


class Stops(models.Model):
    location = models.CharField(max_length=150, null=True, blank=True)
    latitude = models.CharField(max_length=150, null=True, blank=True)
    longitude = models.CharField(max_length=150, null=True, blank=True)
    stop_charge = models.ForeignKey(StopCharges, on_delete=models.CASCADE, null=True, blank=True)
    minutes = models.IntegerField(default=10)
    route_type = models.CharField(choices=ROUTE_TYPES, max_length=50, default=ROUTE_TYPES[0][0])
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def get_stop_charge(self):
        return self.stop_charge.charge_per_minute

    def stop_title(self):
        return f"{self.location} {self.minutes} minutes break"

    def stop_charges(self):
        return self.stop_charge.charge_per_minute * self.minutes

    def __str__(self):
        return self.stop_title()

    class Meta:
        verbose_name = _('Stop')
        verbose_name_plural = _('Stops')


class Route(models.Model):
    trip = models.ForeignKey("Trip", on_delete=models.CASCADE, related_name="routes")
    route_type = models.CharField(choices=ROUTE_TYPES, max_length=50, default=ROUTE_TYPES[0][0])
    departure_latitude = models.CharField(max_length=150, null=True, blank=True)
    departure_longitude = models.CharField(max_length=150, null=True, blank=True)
    departure_city = models.CharField(max_length=150, null=True, blank=True)
    destination_latitude = models.CharField(max_length=150, null=True, blank=True)
    destination_longitude = models.CharField(max_length=150, null=True, blank=True)
    destination_city = models.CharField(max_length=150, null=True, blank=True)
    number_of_stops = models.IntegerField(default=0)
    total_distance = models.CharField(max_length=255, null=True, blank=True)
    total_distance_in_km = models.CharField(max_length=255, null=True, blank=True)
    estimated_time = models.CharField(max_length=20)
    toll_charges = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    bus_stops = models.ManyToManyField(Stops, null=True, blank=True)
    pickup_time = models.CharField(max_length=40, null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)  # when journey start
    drop_off_time = models.CharField(max_length=40, null=True, blank=True)
    drop_off_date = models.DateField(null=True, blank=True)  # when journey start
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def get_stops_charges(self):
        total_charges = 0
        try:
            total_charges_result = self.bus_stops.aggregate(
                total=Sum(F('minutes') if F('minutes') else 0 * F('stop_charge__charge_per_minute') if F(
                    'stop_charge__charge_per_minute') else 0)
            )
            total_charges = total_charges_result.get('total', 0)
        except Exception as ex:
            total_charges = 0
        return total_charges if total_charges else 0

    def get_icon(self):
        if self.route_type == "on_going":
            return "angle-right"
        else:
            return "angle-left"

    class Meta:
        verbose_name = _('Route')
        verbose_name_plural = _('Routes')


class License(models.Model):  #
    license_name = models.CharField(max_length=50, unique=True)
    seat_limit = models.IntegerField()

    def __str__(self):
        return self.license_name

    class Meta:
        verbose_name = _('License')
        verbose_name_plural = _('Licenses')


class Insurance(models.Model):  #
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    coverage_amount = models.DecimalField(max_digits=10, decimal_places=2)
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Insurance')
        verbose_name_plural = _('Insurances')


class TripInsurance(models.Model):
    trip = models.ForeignKey("Trip", on_delete=models.CASCADE, related_name="trip_insurances")
    insurance = models.ManyToManyField(Insurance)
    date_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Trip Insurance')
        verbose_name_plural = _('Trip Insurances')


class TripCategory(models.Model):  #
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Trip Category')
        verbose_name_plural = _('Trip Categories')


class Trip(models.Model):  #
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True, blank=True)
    scale = models.CharField(max_length=50, choices=BUS_CHARGES_SCALE, default=BUS_CHARGES_SCALE[0][0], null=True,
                             blank=True)
    per_scale_charges = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    trip_category = models.ForeignKey(TripCategory, on_delete=models.CASCADE, null=True, blank=True)
    number_passengers = models.IntegerField(default=1)
    number_children = models.IntegerField(default=1)
    number_adults = models.IntegerField(default=1)
    is_driver_required = models.BooleanField(default=True)
    is_id_verified = models.BooleanField(default=True)  # need to discuss with chase
    identity_card = models.FileField(upload_to=trip_path,default="")
    weight_of_luggage = models.DecimalField(max_digits=150, decimal_places=2, default=0)
    is_seat_belts_required = models.BooleanField(default=True)
    is_insurance_required = models.BooleanField(default=False)
    is_trailer_required = models.BooleanField(default=False)
    is_collision_damage_required = models.BooleanField(default=False)
    trip_status = models.CharField(max_length=50, choices=TRIP_STATUS, default=TRIP_STATUS[0][0])
    on_going_date = models.DateField(null=True, blank=True)  # when journey start
    return_date = models.DateField(null=True, blank=True)  # when bus start towards the return city
    bus_returned_date = models.DateField(null=True, blank=True)  # when bus available for other trips
    trip_type = models.CharField(max_length=50, choices=TRIP_TYPE, default=TRIP_TYPE[0][0])
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}"
    def get_identity_card_image(self):
        if not self.identity_card:
            logo = "defaults/no-image.png"
        else:
            logo = self.identity_card
        print(logo)
        return logo
    def get_insurance_premium(self):
        from django.db.models import Sum, DecimalField
        from django.db.models.functions import Coalesce
        if self.is_insurance_required:
            total_premium = self.trip_insurances.aggregate(
                total_premium=Sum(Coalesce('insurance__premium', 0), output_field=DecimalField())
            )['total_premium']
            return float(total_premium) if total_premium is not None else 0.0
        return 0.0

    def get_total_stops(self):
        total_stops = self.routes.annotate(total_stops=Count('bus_stops')).aggregate(sum_stops=Sum('total_stops'))[
            'sum_stops']
        return total_stops if total_stops else 0

    def get_total_passengers(self):
        return self.number_adults + self.number_children

    def get_pickup(self):
        route = self.routes.filter(route_type="on_going").first()
        if not route:
            route = self.routes.first()
        return route.departure_city if route else None

    def get_destination(self):
        route = self.routes.filter(route_type="on_going").first()
        if not route:
            route = self.routes.first()
        return route.destination_city if route else None

    def get_ongoing_date(self):
        route = self.routes.filter(route_type="on_going").first()
        if not route:
            route = self.routes.first()
        return route.pickup_date if route else None

    def get_return_date(self):
        route = self.routes.filter(route_type="return_back").first()
        if not route:
            route = self.routes.first()
        return route.drop_off_date if route else None

    def get_on_trip_direction(self):

        return f"{self.get_pickup()} To {self.get_destination()}"

    def get_trip_total_distance(self):
        total_distance = self.routes.aggregate(
            total=Sum(Cast("total_distance_in_km", FloatField()))
        )['total']
        return total_distance

    def get_self_drive_hours(self):
        hours = 0
        if self.trip_type == TRIP_TYPE[2][0] and self.scale == BUS_CHARGES_SCALE[0][0]:
            pickup_date = self.routes.first()
            pickup_date_time = parse_str_date_time(pickup_date.pickup_date, pickup_date.pickup_time)
            return_date_time = parse_str_date_time(pickup_date.drop_off_date, pickup_date.drop_off_time)
            diff = abs(return_date_time - pickup_date_time)
            hours = math.ceil(diff.total_seconds() / 3600)
        return hours

    def self_drive_price(self):
        if self.trip_type == TRIP_TYPE[2][0] and self.scale == BUS_CHARGES_SCALE[0][0]:
            return round(self.per_scale_charges * self.get_self_drive_hours(), 2)
        return 0

    def get_routes_price(self):
        routes_prices = 0
        if self.trip_type == TRIP_TYPE[2][0] and self.scale == BUS_CHARGES_SCALE[0][0]:
            routes_prices = self.self_drive_price()
        else:
            routes_prices = round(float(self.get_trip_total_distance()) * float(self.per_scale_charges), 2)
        return routes_prices

    def get_routes_stop_charges_price(self):
        amount = 0
        for route in self.routes.all():
            amount += route.get_stops_charges()
        return round(amount, 2)

    def get_trip_tax(self):
        return round(self.get_trip_charges() * float(self.get_tax_charge()), 2)

    def get_service_charge(self):
        return float(settings.SERVICE_CHARGES)

    def get_tax_charge(self):
        return float(settings.TAX_PERCENTAGE / 100)

    def get_sub_total(self):
        return round(self.get_trip_charges() + self.get_trip_tax() + self.get_service_charge(), 2)

    def get_trip_charges(self):
        total_charges = float(self.get_routes_price()) + float(self.get_routes_stop_charges_price()) + float(
            self.get_insurance_premium())
        return total_charges

    class Meta:
        verbose_name = _('Trip')
        verbose_name_plural = _('Trips')


class UserLicense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True, related_name="trip_license")
    license_type = models.ForeignKey(License, on_delete=models.CASCADE)
    license = models.FileField(upload_to=license_path)
    status = models.CharField(choices=LICENSE_STATUS, default=LICENSE_STATUS[0][0], max_length=30)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User License')
        verbose_name_plural = _('UserLicenses')


class Coupons(models.Model):  #
    code = models.CharField(max_length=10, unique=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    one_time_use_per_user = models.BooleanField(default=True)
    minimum_amount = models.DecimalField(max_digits=50, decimal_places=2)
    amount = models.DecimalField(max_digits=50, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')


class Order(models.Model):  #
    order_id = models.CharField(max_length=50, unique=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="order")
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    coupon = models.ForeignKey(Coupons, on_delete=models.CASCADE, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=150, decimal_places=2)
    discount = models.DecimalField(max_digits=50, decimal_places=2)
    grand_total = models.DecimalField(max_digits=50, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, null=True, blank=True, decimal_places=3)
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS, default=ORDER_STATUS[0][0])
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    def get_payment_obj(self):
        return self.order_payments.filter(payment_status=PAYMENT_STATUS[2][0]).first()

    def get_order_date(self):
        return self.get_payment_obj().created_at if self.get_payment_obj() else self.created_at

    def crm_admin_cash(self):
        payment = self.order_payments.filter(payment_gateway=PAYMENT_GATEWAYS[1][0]).first()
        if payment and self.order_status in (ORDER_STATUS[0][0], ORDER_STATUS[1][0]):
            return True
        else:
            return False

    def need_to_pay(self):
        method = self.payment_method()
        if method != PAYMENT_GATEWAYS[1][0] and self.order_status in (ORDER_STATUS[0][0], ORDER_STATUS[1][0]):
            return True
        else:
            return False

    def payment_method(self):
        payment = self.order_payments.filter(payment_status=PAYMENT_STATUS[2][0]).first()
        return payment.payment_gateway if payment else None

    def __str__(self):
        return self.order_id

    def is_refund_applicable(self):
        current_date = timezone.now().date()
        on_going = self.trip.routes.filter(route_type=ROUTE_TYPES[0][0]).first()
        if not on_going:
            return False
        refund = Refund.objects.filter(order=self, refund_status=PAYMENT_STATUS[2][0])
        on_going_refund_time = on_going.pickup_date - timedelta(days=1)
        if not refund and self.order_status == ORDER_STATUS[2][0] and on_going_refund_time > current_date:
            return True
        else:
            return False

    def order_status_color(self):
        if self.order_status == ORDER_STATUS[0][0] or self.order_status == ORDER_STATUS[1][0]:
            return "info"
        elif self.order_status == ORDER_STATUS[2][0]:
            return "success"
        else:
            return "danger"

    def get_order_progress(self):

        payment = self.order_payments.filter(payment_id__isnull=False).first()

        progress = [{"text": "Select Locations", "class": "step-bar-active"},
                    {"text": "Confirm Booking", "class": "step-bar-active"}]
        if self.order_status in ["InProgress", "Confirmed", "In Progress"]:
            progress.append({"text": "Order Confirmed", "class": "step-bar-active"})
        elif self.order_status in ["Rejected", "Cancelled"]:
            progress.append({"text": f"Order {self.order_status}", "class": "red"})
        else:
            progress.append({"text": f"Order Pending", "class": "warning"})
        if payment:
            if payment.payment_status in ["InProgress", "Paid", "In Progress"]:
                progress.append({"text": "Payment Confirmed", "class": "step-bar-active"})
            elif payment.payment_status in ["Rejected", "Cancelled"]:
                progress.append({"text": f"Payment {payment.payment_status}", "class": "red"})
            else:
                progress.append({"text": f"Payment Pending", "class": "warning"})
        else:

            progress.append({"text": f"Payment Pending", "class": "warning"})
            progress.append({"text": "Order Confirmed", "class": ""})

        return progress

    def get_customer_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_payment(self):
        return self.order_payments.first()

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def save(self, *args, **kwargs):
        if not self.order_id:
            today = timezone.now().strftime('%Y%m%d')
            latest_order = Order.objects.filter(order_id__startswith=today).order_by('-id').first()
            if latest_order:

                latest_order_id = latest_order.order_id[8:]
                if not latest_order_id:
                    latest_order_id = 1

                new_order_id = f"{today}{int(latest_order_id) + 1}"
            else:
                new_order_id = f"{today}1"
            self.order_id = new_order_id
        super(Order, self).save(*args, **kwargs)


class Payments(models.Model):  #
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_payments")
    payment_gateway = models.CharField(max_length=50, null=True, blank=True, choices=PAYMENT_GATEWAYS)
    payment_id = models.CharField(max_length=150, null=True, blank=True)
    payment_intent_id = models.CharField(max_length=150, null=True, blank=True)
    payment_intent_secret = models.CharField(max_length=150, null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default=PAYMENT_STATUS[0][0])
    created_at = models.DateTimeField(default=timezone.now)
    paid_amount = models.DecimalField(max_digits=10, null=True, blank=True, decimal_places=3)
    modified_at = models.DateTimeField(auto_now=True)

    def payment_status_color(self):
        if self.payment_status == PAYMENT_STATUS[0][0] or self.payment_status == PAYMENT_STATUS[1][0]:
            return "info"
        elif self.payment_status == PAYMENT_STATUS[2][0]:
            return "success"
        else:
            return "danger"

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')


class Refund(models.Model):  #
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refund")
    refund_id = models.CharField(max_length=150, null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=150, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=50, decimal_places=2)
    refund_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default=PAYMENT_STATUS[0][0])
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Refund')
        verbose_name_plural = _('Refunds')


class FeaturedTrips(models.Model):  #
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="bus_featured_trips", null=True, blank=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Featured Trip')
        verbose_name_plural = _('Featured Trips')


class Cities(models.Model):  #
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')


class FaqsCategory(models.Model):  #
    type = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.type

    class Meta:
        verbose_name = _('Faqs Category')
        verbose_name_plural = _('Faq Categories')


class Faqs(models.Model):  #
    type = models.ForeignKey(FaqsCategory, on_delete=models.CASCADE, related_name="Category_faqs")
    question = models.CharField(max_length=200)
    answer = models.CharField(max_length=500)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Faq')
        verbose_name_plural = _('Faqs')


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Xero(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.CharField(max_length=255, default="")
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    expire_token = models.DateTimeField(null=True, blank=True)
    tenant_id = models.CharField(max_length=255, null=True, blank=True)
    account_id = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, default="")

    def is_valid_token(self):
        if self.expire_token is not None and self.expire_token > timezone.now():
            return True
        elif self.refresh_token:
            client = XeroClient()
            res = client.get_refresh_token(self.refresh_token)
            return True if res else False
        else:
            return False
