from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import RouteForm
from .models import *
from django.contrib.auth.models import Group

admin.site.unregister(Group)

admin.site.site_header = "Buses Plus"
admin.site.site_title = "Buses Plus"
admin.site.index_title = "Buses Plus|SuperAdminPanel"


class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name']
    list_filter = ['is_active', 'is_staff']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('full_name', 'phone_number', 'driving_license', 'profile')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    ordering = ['email']
    # change_form_template = 'admin/custom_user_change_form.html'  # Create the template in your templates directory
    readonly_fields = ['driving_license', 'profile', 'is_active', 'is_staff', 'is_superuser', 'last_login',
                       'date_joined','is_order_user']

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ['email', 'full_name', 'phone_number', 'password', 'groups',
                                           'user_permissions']
        return self.readonly_fields


class CustomBusAdmin(admin.ModelAdmin):
    list_display = ['bus_number', 'number_seats', 'is_available', 'company_name', 'name', 'bus_model']
    search_fields = ['bus_number', 'company_name']
    list_filter = ['is_available', 'company_name','self_drive_available']
    fieldsets = (
        (None, {'fields': ('bus_number', 'number_seats', 'is_available','bus_status', 'company_name','self_drive_available')}),
        ('Bus Details', {'fields': ('name', 'bus_model', 'bus_emergency_number', 'luggage_capacity')}),
        ('Other', {'fields': ('tag',)}),
    )

    # readonly_fields = ['bus_emergency_number', 'luggage_capacity', 'tag', 'scale', 'per_scale_charges']

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ['bus_number', 'number_seats', 'is_available', 'company_name', 'name',
                                           'bus_model']
        return self.readonly_fields

    ordering = ['bus_number']


class RouteAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        if obj:  # If editing an existing Route
            return RouteForm
        return super(RouteAdmin, self).get_form(request, obj, **kwargs)

    list_display = ["id", 'trip', 'route_type', 'departure_city', 'destination_city', 'number_of_stops',
                    'total_distance_in_km', 'estimated_time']
    list_filter = ['trip', 'route_type', 'departure_city', 'destination_city']
    search_fields = ['trip__name', 'departure_city', 'destination_city']
    # readonly_fields = ['total_distance_in_km']
    date_hierarchy = 'pickup_date'


class BusImagesAdmin(admin.ModelAdmin):
    list_display = ['bus', 'image']

    search_fields = ['bus__bus_number']

    list_filter = ['bus__bus_number']


class StopChargesAdmin(admin.ModelAdmin):
    list_display = ['stop_title', 'charge_per_minute']

    search_fields = ['stop_title']

    list_filter = ['stop_title']


class StopsAdmin(admin.ModelAdmin):
    list_display = ['stop_title', 'stop_charge', 'minutes', 'route_type','get_stop_charge',"stop_charges"]
    search_fields = ['location']
    list_filter = ['route_type']
    fieldsets = (
        (None, {'fields': ('location', 'latitude', 'longitude')}),
        ('Stop Details', {'fields': ('stop_charge', 'minutes', 'route_type')}),
    )


class LicenseAdmin(admin.ModelAdmin):
    list_display = ['license_name', 'seat_limit']
    search_fields = ['license_name']


class TripInsuranceAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip', 'insurance', 'date_time']
    search_fields = ['trip__bus__bus_name', 'insurance__name']

class XeroAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_valid_token']
    readonly_fields = ['admin_user','organization','refresh_token','expire_token','tenant_id','account_id','account_name']

class TripInsuranceAdmin(admin.ModelAdmin):
    list_display = ['trip', 'date_time']
    search_fields = ['trip__bus__bus_name', 'insurance__name']


class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'bus', 'scale', 'user', 'trip_status', 'on_going_date', 'return_date']
    list_filter = ['bus', 'scale', 'user', 'trip_status']
    search_fields = ['bus__bus_name', 'user__username']


class UserLicenseAdmin(admin.ModelAdmin):
    list_display = ['user', 'trip', 'license_type', 'status']
    search_fields = ['user__username', 'trip__bus__bus_name', 'license_type__license_name']


class CouponsAdmin(admin.ModelAdmin):
    list_display = ['code', 'start_date', 'end_date', 'is_active', 'one_time_use_per_user', 'minimum_amount', 'amount']
    search_fields = ['code']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_id', 'trip', 'first_name', 'last_name', 'email', 'phone_number', 'coupon', 'sub_total',
                    'discount', 'grand_total', 'order_status']
    list_filter = ['trip', 'order_status']
    search_fields = ['order_id', 'first_name', 'last_name', 'email', 'phone_number']


class PaymentsAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_gateway', 'payment_id', 'payment_intent_id', 'payment_status']
    list_filter = ['order', 'payment_gateway', 'payment_status']
    search_fields = ['order__order_id', 'payment_id', 'payment_intent_id']


class RefundAdmin(admin.ModelAdmin):
    list_display = ['order', 'refund_amount', 'total_amount', 'refund_status']
    list_filter = ['order', 'refund_status']
    search_fields = ['order__order_id']


class FeaturedTripsAdmin(admin.ModelAdmin):
    list_display = ['trip', 'price', 'discount_price', 'rating']
    search_fields = ['trip']


class CitiesAdmin(admin.ModelAdmin):
    list_display = ['city', 'latitude', 'longitude']
    search_fields = ['city']
    list_filter = ['is_active']


class ContactUsAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject"]
    search_fields = ["name", "email", "subject"]


class FaqsAdmin(admin.ModelAdmin):
    list_display = ['type', 'question', 'answer']
    search_fields = ['type', 'question']


admin.site.register(FeaturedTrips, FeaturedTripsAdmin)
admin.site.register(Cities, CitiesAdmin)
admin.site.register(Faqs, FaqsAdmin)

admin.site.register(Payments, PaymentsAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ContactUs, ContactUsAdmin)
admin.site.register(UserLicense, UserLicenseAdmin)
admin.site.register(Coupons, CouponsAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(TripInsurance, TripInsuranceAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(Insurance)
admin.site.register(BusCharges)
admin.site.register(TripCategory)
admin.site.register(Route, RouteAdmin)
admin.site.register(BusImages, BusImagesAdmin)
admin.site.register(StopCharges, StopChargesAdmin)
admin.site.register(Stops, StopsAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Bus, CustomBusAdmin)
admin.site.register(FaqsCategory)
admin.site.register(Xero, XeroAdmin)
