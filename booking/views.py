import re

from django.db.models import Q
from cryptography.fernet import Fernet
from urllib.parse import urlencode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from booking.models import *
from crm.Integrations.GoogleAPI import GoogleAPI
from crm.models import GoogleAuth

from .forms import *

from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.template.loader import render_to_string, get_template
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from booking.utils import send_email, add_form_errors_messages
from booking.tasks import *
from django.utils.translation import gettext_lazy as _

COUNTRY = "Australia"


# messages.add_message(request, messages.INFO, "Hello world.")


def index(request):
    return render(request, "booking/index.html")


class IndexPageView(View):
    def get(self, request):
        # create_xero_invoice(87)
        featuredTrips = FeaturedTrips.objects.all()
        return render(request, 'booking/index.html',
                      {"featuredTrips": featuredTrips, })


class Booking(View):
    buses_per_page = 10

    def get(self, request):
        page_obj = []
        show_buses = settings.IS_BUSES_SHOW_TO_USER

        buses = Bus.objects.filter(is_available=True).order_by("id")
        paginator = Paginator(buses, self.buses_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {"buses": page_obj, "show_buses": show_buses}
        return render(request, "booking/booking.html", context)

    def post(self, request):
        pickup = request.POST.get("pickup")

        destination = request.POST.get("destination")
        selectedBusIds = request.POST.get("selectedBusIds")
        pickup_date = request.POST.get("pickup_date")
        pickup_time = request.POST.get("pickup_time")
        return_date = request.POST.get("return_date")
        drop_off_date = request.POST.get("drop_off_date")
        drop_off_time = request.POST.get("drop_off_time")
        trip_type = request.POST.get("trip_type")
        adult_number = int(request.POST.get("adult_number", 0))
        child_number = int(request.POST.get("child_number", 0))
        bikes_number = int(request.POST.get("bikes_number", 0))
        total_number = adult_number + child_number
        show_buses = settings.IS_BUSES_SHOW_TO_USER
        page_obj = []
        if trip_type == "3" or trip_type == 3:
            pickup = settings.SELF_DRIVE_PICKUP_ADDRESS
            destination = settings.SELF_DRIVE_PICKUP_ADDRESS

        buses = Bus.objects.filter(is_available=True).order_by("id")
        if total_number:
            buses = buses.filter(number_seats__gte=total_number)

        paginator = Paginator(buses, self.buses_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {"buses": page_obj, "return_date": return_date, "drop_off_time": drop_off_time,
                   "drop_off_date": drop_off_date, "pickup_time": pickup_time, "pickup": pickup,
                   "bikes_number": bikes_number, "child_number": child_number,
                   "destination": destination, "pickup_date": pickup_date, "adult_number": adult_number,
                   "trip_type": trip_type, "show_buses": show_buses, "selectedBusIds": selectedBusIds}
        return render(request, "booking/booking.html", context)


class EditBookingView(View):
    buses_per_page = 10

    def get(self, request, pk):
        trip = Trip.objects.filter(id=pk, user=request.user).first()
        if not trip:
            messages.add_message(request, messages.ERROR, _("Invalid Trip"))
            return redirect("/")
        order = Order.objects.filter(trip=trip).first()
        if order and order.order_payments.filter(payment_id__isnull=False).exists():
            messages.add_message(request, messages.ERROR, _("You cannot edit booking after order confirmation"))
            return redirect("/")
        pickup = trip.get_pickup()
        destination = trip.get_destination()

        selectedBusIds = trip.bus.id
        on_going = trip.routes.filter(route_type="on_going").first()
        return_back = trip.routes.filter(route_type="return_back").first()
        return_date = None
        pickup_date = None
        pickup_time = None
        drop_off_date = None
        drop_off_time = None
        if on_going:
            pickup_date = on_going.pickup_date
            pickup_time = on_going.pickup_time
            drop_off_date = request.POST.get("drop-off_date")
            drop_off_time = request.POST.get("drop-off_time")
        if return_back:
            return_date = return_back.pickup_date

        trip_type = "2" if trip.is_two_way_trip else "1"
        show_buses = settings.IS_BUSES_SHOW_TO_USER
        if trip_type == "3" or trip_type == 3:
            pickup = settings.SELF_DRIVE_PICKUP_ADDRESS
            destination = settings.SELF_DRIVE_PICKUP_ADDRESS
        page_obj = []

        buses = Bus.objects.filter(is_available=True).order_by("id")
        paginator = Paginator(buses, self.buses_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {"buses": page_obj, "return_date": return_date, "drop_off_time": drop_off_time,
                   "drop_off_date": drop_off_date, "pickup_time": pickup_time, "pickup": pickup,
                   "destination": destination, "daterange_single": pickup_date,
                   "trip_type": trip_type, "selectedBusIds": selectedBusIds, "show_buses": show_buses}
        return render(request, "booking/edit-booking.html", context)

    def post(self, request, pk):
        trip = Trip.objects.filter(id=pk).first()
        if not trip:
            messages.add_message(request, messages.ERROR, _("Invalid Trip"))
            return redirect("/")
        order = Order.objects.filter(trip=trip).first()
        if order and order.order_payments.filter(payment_id__isnull=False).exists():
            messages.add_message(request, messages.ERROR, _("You cannot edit booking after order confirmation"))
            return redirect("/")
        pickup = request.POST.get("pickup")
        destination = request.POST.get("destination")
        selectedBusIds = request.POST.get("selectedBusIds")
        pickup_date = request.POST.get("pickup_date")
        pickup_time = request.POST.get("pickup_time")
        return_date = request.POST.get("return_date")
        drop_off_date = request.POST.get("drop-off_date")
        drop_off_time = request.POST.get("drop-off_time")
        trip_type = request.POST.get("trip_type")
        adult_number = int(request.POST.get("adult_number", 0))
        child_number = int(request.POST.get("child_number", 0))
        bikes_number = int(request.POST.get("bikes_number", 0))
        total_number = adult_number + child_number
        show_buses = settings.IS_BUSES_SHOW_TO_USER
        if trip_type == "3" or trip_type == 3:
            pickup = settings.SELF_DRIVE_PICKUP_ADDRESS
            destination = settings.SELF_DRIVE_PICKUP_ADDRESS
        page_obj = []

        buses = Bus.objects.filter(is_available=True).order_by("id")
        if total_number:
            buses = buses.filter(number_seats__gte=total_number)

        paginator = Paginator(buses, self.buses_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context = {"buses": page_obj, "return_date": return_date, "drop_off_time": drop_off_time,
                   "drop_off_date": drop_off_date, "pickup_time": pickup_time, "pickup": pickup,
                   "bikes_number": bikes_number, "adult_number": adult_number, "child_number": child_number,
                   "destination": destination, "daterange_single": pickup_date, "adult_number": adult_number,
                   "trip_type": trip_type, "show_buses": show_buses}
        return render(request, "booking/booking.html", context)


@csrf_exempt
def get_more_buses(request):
    amount = request.POST.get("amount")
    seating_capacity = request.POST.get("seating_capacity")
    filter_by = request.POST.get("filter_by")

    amount_numbers = re.findall(r'\d+', amount)
    capacity = re.findall(r'\d+', seating_capacity)
    low_amount = int(amount_numbers[0])
    low_capacity = int(capacity[0])
    height_amount = int(amount_numbers[1])
    height_capacity = int(capacity[1])
    buses = Bus.objects.filter(is_available=True, bus_charges__per_scale_charges__gte=low_amount,
                               bus_charges__per_scale_charges__lte=height_amount
                               , number_seats__gte=low_capacity, number_seats__lte=height_capacity).order_by("id")
    if filter_by in BUS_FILTERS:
        buses = buses.filter(tag=BUS_FILTERS[filter_by])

    if filter_by in BUS_FILTER_SORT:
        buses = buses.order_by(BUS_FILTER_SORT[filter_by])

    buses_per_page = 10
    paginator = Paginator(buses, buses_per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {"buses": page_obj}
    html = render_to_string("render-templates/buses_list.html", context)
    return JsonResponse({"data": html, 'status': 'ok'})


class CheckoutView(View):
    def get(self, request):
        return render(request, 'booking/checkout.html')


class PricingView(View):
    def get(self, request):
        return render(request, 'booking/pricing.html')


class PaymentCompleteView(View):
    def get(self, request):
        return render(request, 'paymentComplete.html')


class PaymentCashView(View):

    def post(self, request):
        order_id = request.POST.get("order_id")
        if not order_id:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("/")
        order = Order.objects.filter(order_id=order_id, trip__user=request.user,
                                     order_status=ORDER_STATUS[0][0]).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("/")
        payments = order.order_payments.all()
        order.order_status = ORDER_STATUS[1][1]
        for pay in payments:
            pay.payment_gateway = PAYMENT_GATEWAYS[1][0]
            pay.payment_status = PAYMENT_STATUS[1][0]
            pay.save()
        order.save()
        return render(request, 'booking/payment-received.html', {"order": order})


class PaymentReceivedView(View):

    def get(self, request, pk):
        payment_intent = request.GET.get("payment_intent")

        redirect_status = request.GET.get("redirect_status")
        if payment_intent or redirect_status:
            return redirect("payment-received", pk)
        order = Order.objects.filter(order_id=pk, trip__user=request.user)

        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("/")

        return render(request, 'paymentReceived.html', {"order": order})


class ErrorPageView(View):

    def get(self, request):
        return render(request, 'booking/pages-404.html')


class BaggagePageView(View):
    def get(self, request):
        return render(request, 'booking/baggage.html')


class ContactPageView(View):

    def get(self, request):
        form = ContactForm()

        return render(request, 'booking/contact.html', {"form": form})

    def post(self, request):
        form = ContactForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, _("Thank you for connecting us, we will reachout soon"))

            return redirect("/")
        else:
            add_form_errors_messages(form, request)
        return render(request, 'booking/contact.html', {"form": form})


class TripReservationPageView(View):
    def get(self, request):
        return render(request, 'booking/trip-reservation.html')


class BusFleetPageView(View):
    def get(self, request):
        return render(request, 'booking/bus-fleet.html')


class BlogSinglePageView(View):
    def get(self, request):
        return render(request, 'booking/blog-single.html')


class BlogSidebarPageView(View):

    def get(self, request):
        return render(request, 'booking/blog-sidebar.html')


class AboutUsPageView(View):

    def get(self, request):
        return render(request, 'booking/about.html')


class FaqPageView(View):
    def get(self, request):
        faqs = FaqsCategory.objects.all()
        return render(request, 'booking/faq.html', {'faqs': faqs})


class PaymentCompletePageView(View):
    def get(self, request):
        return render(request, 'booking/payment-complete.html')


class PaymentReceivedPageView(View):
    def get(self, request, pk):
        payment_intent = request.GET.get("payment_intent")

        redirect_status = request.GET.get("redirect_status")
        if payment_intent or redirect_status:
            if not request.user.is_authenticated:
                payment = Payments.objects.filter(payment_intent_id=payment_intent).first()
                if payment:
                    user = payment.order.trip.user
                    login(request, user)
            return redirect("payment-received", pk)
        if not request.user.is_authenticated:
            return redirect("login")
        order = Order.objects.filter(Q(id=pk) | Q(order_id=pk), trip__user=request.user).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("/")
        return render(request, 'booking/payment-received.html', {"order": order})


class RouteMapPageView(View):
    def get(self, request):
        return render(request, 'booking/route-map.html')


class CustomerWithDisabilitiesPageView(View):
    def get(self, request):
        cat = FaqsCategory.objects.filter(type="Customers with Disabilities").first()
        faqs = []
        if cat:
            faqs = cat.Category_faqs.all()
        return render(request, 'booking/customer-with-disabilities.html', {'faqs': faqs})


class PaymentAndTicketsPageView(View):
    def get(self, request):
        cat = FaqsCategory.objects.filter(type="Payment").first()
        if cat:
            faqs = cat.Category_faqs.all()
        return render(request, 'booking/payment-and-ticket.html', {'faqs': faqs})


class OnBoardEntertainmentPageView(View):
    def get(self, request):
        return render(request, 'booking/on-board-entertainment.html')


class BusFeaturesPageView(View):
    def get(self, request):
        return render(request, 'booking/bus-features.html')


class ManageMyBookingPageView(View):

    def get(self, request):
        return render(request, 'booking/manage-my-booking.html')


class SendEmailView(View):

    def get(self, request):
        form = ResetForm()
        return render(request, 'registration/password-reset-form.html', {"form": form})

    def post(self, request):
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['username']
            user = User.objects.filter(email=email).first()

            if user is None:
                messages.add_message(request, messages.ERROR, "Email dose not  exist")
            else:
                reset_token = default_token_generator.make_token(user)
                reset_link_params = {
                    'token': reset_token,
                    'user_id': urlsafe_base64_encode(force_bytes(user.id)),
                }
                reset_link = f"{request.META['REMOTE_ADDR']}/password-reset-confirm/?{urlencode(reset_link_params)}"

                subject = 'Password Reset Request'
                message = f'Click the following link to reset your password: {reset_link}'
                print(reset_link)
                recipient_list = [email]
                send_email(subject, message, recipient_list)

                return redirect("password-reset-done")

        return render(request, 'registration/password-reset-form.html', {'form': form})


class PasswordResetConfirmPageView(View):

    def get(self, request):
        token = request.GET.get('token')
        user_id = request.GET.get('user_id')

        try:
            user_id = urlsafe_base64_decode(user_id).decode()
            user = User.objects.get(id=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            form = ResetPasswordForm()
            return render(request, 'registration/password-reset-confirm.html', {'form': form})
        else:
            messages.error(request, "Invalid reset link.")
            return redirect("password-reset-form")

    def post(self, request):
        token = request.GET.get('token')
        user_id = request.GET.get('user_id')
        form = ResetPasswordForm(request.POST)
        try:
            user_id = urlsafe_base64_decode(user_id).decode()
            user = User.objects.get(id=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user and default_token_generator.check_token(user, token) and form.is_valid():
            new_password = form.cleaned_data['password1']
            user.set_password(new_password)
            user.save()
            messages.add_message(request, messages.SUCCESS, "Password Reset Successfully")
            return redirect("password-reset-complete")
        else:
            return render(request, 'registration/password-reset-confirm.html', {'form': form})


class PasswordResetDonePageView(View):

    def get(self, request):
        return render(request, 'registration/password-reset-done.html')


class PasswordResetCompletePageView(View):

    def get(self, request):
        return render(request, 'registration/password-reset-complete.html')


class AdminDashboardPageView(View):
    def get(self, request):
        return render(request, 'crm/home/user.html')


@method_decorator(login_required, name='dispatch')
class MyOrderPageView(View):
    def get(self, request):
        user = request.user
        trips = Trip.objects.filter(user=user)
        orders = Order.objects.filter(trip__user=user)
        return render(request, 'booking/my-orders.html', {"orders": orders, "trips": trips})


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/")
        return render(request, 'booking/login.html')

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("/")
        form = CustomUserLoginForm(request.POST)
        next = request.GET.get("next", "index")
        rememberchb = request.POST.get("rememberchb", "off")
        rememberme = rememberchb == "on"
        if form.is_valid():
            email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if not rememberme:
                    request.session.set_expiry(0)
                return redirect(next)
            else:
                form.add_error('password', "Invalid email or password.")

        return render(request, 'booking/login.html', {'form': form})


class SignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/")
        form = CustomUserSignupForm()
        return render(request, 'booking/sign_up.html', {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("/")
        if request.method == 'POST':
            form = CustomUserSignupForm(request.POST)
            if form.is_valid():
                form.save()
                messages.add_message(request, messages.SUCCESS, "Account Created")
                return redirect("login")
            else:
                print(form.errors)

                return render(request, 'booking/sign_up.html', {'form': form})
        else:
            return redirect("signup")


class ConfirmBooking(View):
    def get(self, request, pk):
        trip = Trip.objects.filter(id=pk).first()
        if not trip:
            messages.add_message(request, messages.ERROR, _("Invalid Trip"))
            return redirect("/")
        order = Order.objects.filter(trip=trip).first()
        if order and order.order_payments.filter(payment_id__isnull=False).exists():
            messages.add_message(request, messages.ERROR, _("This trip is already configured"))
            return redirect("/")
        stops_type = StopCharges.objects.all()
        all_stops = []

        for route in trip.routes.all():
            all_stops.extend(route.bus_stops.all())

        form = TripForm(instance=trip)

        license_form = UserLicenseForm(trip=trip or None, instance=trip.trip_license.first())
        insurance_form = UseInsuranceForm(instance=trip.trip_insurances.first())
        return render(request, "booking/confirm-booking.html",
                      {"insurance_form": insurance_form, "form": form, "trip": trip, "stops_type": stops_type,
                       "all_stops": all_stops, "license_form": license_form})

    def post(self, request, pk):
        return render(request, "booking/confirm-booking.html")


class CheckoutView(View):
    def get(self, request, pk):
        return redirect("confirm-booking", pk)

    def post(self, request, pk):

        # trip_id = request.POST.get('trip')
        trip = Trip.objects.filter(id=pk).first()
        form = TripForm(request.POST or None, request.FILES, instance=trip or None)

        if form.is_valid():
            trip = form.save()
        else:
            add_form_errors_messages(form, request)
            return redirect("confirm-booking", trip.id)
        trip.number_passengers == trip.number_adults + trip.number_children
        show_buses = settings.IS_BUSES_SHOW_TO_USER
        if not trip.bus:
            bus = Bus.objects.filter(number_seats__gte=trip.number_adults + trip.number_children,
                                     luggage_capacity__gte=trip.weight_of_luggage).order_by("number_seats",
                                                                                            "luggage_capacity").first()
            if not bus:
                messages.add_message(request, messages.ERROR,
                                     _("So sorry we do not available at this  moment please try again later!"))
                return redirect("confirm-booking", trip.id)
            trip.bus = bus
            trip.save()
        trip_type_charge = BUS_CHARGES_SCALE[1][0]
        if trip.trip_type == TRIP_TYPE[2][0]:
            trip_type_charge = BUS_CHARGES_SCALE[0][0]
        scale_bus = trip.bus.bus_charges.filter(scale=trip_type_charge).first()
        if scale_bus:
            scale = scale_bus.scale
            scale_charge = scale_bus.per_scale_charges
        else:
            scale = BUS_CHARGES_SCALE[1][0]
            scale_charge = 0
        trip.per_scale_charges = scale_charge
        trip.scale = scale
        trip.save()
        if not trip.per_scale_charges:
            messages.add_message(request, messages.ERROR, _("Something wrong with a bus charges please try with  "
                                                            "another vehicle"))
            return redirect("/")
        if not trip:
            messages.add_message(request, messages.ERROR, _("Invalid Trip"))
            return redirect("/")

        order = Order.objects.filter(trip=trip).first()
        if order and order.order_payments.filter(payment_id__isnull=False).exists():
            messages.add_message(request, messages.ERROR, _("This trip is already configured"))
            return redirect("/")

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        coupon_code = request.POST.get('coupon_code')
        if not request.user.is_authenticated:
            user, new_user_create = User.objects.get_or_create(email=email,
                                                               defaults={"first_name": first_name,
                                                                         "phone_number": phone_number,
                                                                         "last_name": last_name, "is_order_user": True})
            login(request, user)
        else:
            user = request.user
        trip.user = user
        trip.save()
        license_form = UserLicenseForm(request.POST, request.FILES, trip=trip, user=user,
                                       instance=trip.trip_license.first() or None)

        if not trip.is_driver_required:
            if license_form.is_valid():
                license_form.save()
            else:
                add_form_errors_messages(license_form, request)
                return redirect("confirm-booking", trip.id)
        insurance_form = UseInsuranceForm(data=request.POST, instance=trip.trip_insurances.first() or None)
        insurance = request.POST.getlist("insurance")
        if trip.is_insurance_required:
            if insurance_form.is_valid():
                instance = insurance_form.save(commit=False)
                instance.trip = trip
                instance.save()
                instance.insurance.set(insurance)
            else:
                add_form_errors_messages(insurance_form, request)
                return redirect("confirm-booking", trip.id)

        try:
            coupon = Coupons.objects.get(code=coupon_code)
            current_date = timezone.now()
            if coupon.start_date > current_date:
                coupon = None
                messages.add_message(request, messages.INFO,
                                     _("This Coupon isn't valid yet, it will start from {start_date}").format(
                                         start_date=coupon.start_date.date()))
            elif coupon.end_date < current_date:
                coupon = None
                messages.add_message(request, messages.INFO, _("Coupon has expired"))
            elif coupon.minimum_amount > trip.get_trip_charges():
                coupon = None
                messages.add_message(request, messages.INFO, _("Coupon doesn't meet the minimum requirements"))
        except Coupons.DoesNotExist:
            coupon = None

        if coupon and coupon.one_time_use_per_user:
            orders_list = Order.objects.filter(trip__user=user, coupon=coupon)
            if orders_list:
                coupon = None
                messages.add_message(request, messages.INFO, _("Coupon has already been used and cannot be used again"))

        sub_total = trip.get_sub_total()
        discount = coupon.amount if coupon else 0
        grand_total = sub_total - discount

        order, created = Order.objects.update_or_create(trip=trip,
                                                        defaults={"first_name": first_name, "last_name": last_name,
                                                                  "email": email, "phone_number": phone_number,
                                                                  "coupon": coupon,
                                                                  "sub_total": sub_total, "discount": discount,
                                                                  "grand_total": grand_total})

        bus = order.trip.bus
        bus.is_available = False
        bus.bus_status = BUS_STATUS[1][0]
        bus.save()
        send_order_confirmation.delay(order.id, user.id)
        return redirect("payment", order.order_id)


class PaymentView(View):

    def get(self, request, pk):

        order = Order.objects.filter(order_id=pk, trip__user=request.user).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("/")

        payment = Payments.objects.filter(order=order, payment_id__isnull=False)
        if payment:
            messages.add_message(request, messages.INFO, _("Order already paid"))
            return redirect("/")
        return render(request, "booking/payment.html", {"order": order})


class Logout(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.add_message(request, messages.SUCCESS, _("Logout Successfully"))
        else:
            messages.add_message(request, messages.SUCCESS, _("Please login first"))
        return redirect("login")


class RefundOrder(View):
    def post(self, request):
        order_id = request.POST.get("order_id")
        if not order_id:
            messages.add_message(request, messages.ERROR, _("Unable to Process you refund request"))
            return redirect("my-order")
        order = Order.objects.filter(id=order_id, order_status=ORDER_STATUS[2][0], trip__user=request.user).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order"))
            return redirect("my-order")
        if Refund.objects.filter(Q(refund_status=PAYMENT_STATUS[0][0]) | Q(refund_status=PAYMENT_STATUS[1][0]),
                                 order=order).exists():
            messages.add_message(request, messages.ERROR, _("Your Refund request already has been initiated"))
            return redirect("my-order")
        if not order.is_refund_applicable():
            messages.add_message(request, messages.ERROR, _("Unable to Process you refund request"))
            return redirect("my-order")
        order.order_status = ORDER_STATUS[6][0]
        trip = order.trip
        trip.trip_status = TRIP_STATUS[4][0]
        trip.save()
        order.save()

        refund = Refund.objects.create(order=order, refund_amount=order.paid_amount, total_amount=order.paid_amount,
                                       refund_status=PAYMENT_STATUS[0][0])
        send_refund_email_init.delay(refund.id)
        messages.add_message(request, messages.SUCCESS, _("Your Refund request has been initiated"))
        return redirect("my-order")


class ScheduleMeeting(View):
    def get(self, request):
        return render(request, "booking/schedule-meeting.html")

    def post(self, request):
        duration = 30
        title = request.POST.get("title", "")
        email = request.POST.get("email", "")
        description = request.POST.get("description", "")
        date_str = request.POST.get("date", "")
        start_time = request.POST.get("start_time", "")
        start_datetime = datetime.strptime(f"{date_str}T{start_time}", "%Y-%m-%dT%I:%M %p")

        end_datetime = start_datetime + timedelta(minutes=duration)

        # Format the calculated end time
        end_time = end_datetime.strftime("%H:%M")

        start_time = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        end_time = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': str(start_time),
                'timeZone': 'Australia/Sydney',
            },
            'end': {
                'dateTime': str(end_time),  # You can calculate end_time based on the duration if needed
                'timeZone': 'Australia/Sydney',
            },
            'attendees': [
                {'email': email},
            ],
        }
        api = GoogleAPI()
        res = api.schedule_gmail_event(gmail=GoogleAuth.objects.first(),event=event)
        if res:
            messages.add_message(request, messages.SUCCESS, _("Invitation link send to  your  email"))
        else:
            messages.add_message(request, messages.ERROR, _("Your are not able schedule meeting now, Please try  "
                                                            "again later"))
        return redirect("/")
