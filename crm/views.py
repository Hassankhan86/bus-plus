import json
import calendar
import uuid
from decimal import Decimal

from django.db.models.functions import ExtractMonth, ExtractDay, ExtractYear
from django.shortcuts import render, redirect, get_object_or_404
from booking.models import *
from datetime import datetime, timedelta
from django.views import View
from django.views.generic import ListView, DeleteView, DetailView
from rest_framework.response import Response
from crm.api.views import calculate_earnings
from crm.forms import *
from booking.utils import add_form_errors_messages
from django.db.models import Q, F, Sum, Count, Avg
from django.db import transaction
from rest_framework.authtoken.models import Token

import pandas as pd
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import random
import string
from booking.models import Payments, Order
from booking.CONSTANT import *
from booking.tasks import send_order_payment_confirmation, create_xero_invoice
from crm.models import GoogleAuth
from crm.Integrations.GoogleAPI import GoogleAPI

# Create your views here.

def dashboard(request):
    current_date = timezone.now()
    recent_20_orders = Order.objects.order_by('created_at')[:20]

    order_data = Order.objects.annotate(month=ExtractMonth('created_at'), year=ExtractYear('created_at')).values(
        'month', 'year').annotate(total_earnings=Sum('grand_total')).order_by('year', 'month')

    available_months = []
    available_years = []
    for entry in order_data:
        month_name = calendar.month_name[entry['month']]
        year = entry['year']
        if month_name not in available_months:
            available_months.append(month_name)
        if year not in available_years:
            available_years.append(year)

    order_data = Order.objects.filter(
        created_at__month=current_date.month,
        created_at__year=current_date.year
    )
    earnings_data = calculate_earnings(order_data, current_date.year, current_date.month)

    listOfLabels = list(earnings_data.keys())
    listOfValues = json.dumps(list(earnings_data.values()))

    top_pickup_locations = Order.objects.annotate(
        pickup=F('trip__routes__departure_city')
    ).values('pickup').annotate(total_earnings=Sum('grand_total')).order_by('-total_earnings')[:3]
    for location in top_pickup_locations:
        city_country = location['pickup'].split(', ')
        location['pickup'] = city_country[0]
    top_destination_locations = Order.objects.annotate(
        destination=F('trip__routes__destination_city')
    ).values('destination').annotate(total_earnings=Sum('grand_total')).order_by('-total_earnings')[:3]

    top_pickup_locations = [
        {'pickup': str(location['pickup'].split(",")[0]), 'total_earnings': location['total_earnings']} for location in
        top_pickup_locations]
    top_destination_locations = [
        {'destination': str(location['destination'].split(",")[0]), 'total_earnings': location['total_earnings']} for
        location in top_destination_locations]
    while len(top_destination_locations) < 3:
        top_destination_locations.append({
            'destination': 'No City',
            'total_earnings': 0
        })
    while len(top_pickup_locations) < 3:
        top_pickup_locations.append({
            'pickup': 'No City',
            'total_earnings': 0
        })
    previous_month_start = (current_date - timedelta(days=current_date.day)).replace(day=1)
    previous_month_end = previous_month_start + timedelta(days=31)
    current_orders_count = Order.objects.count()
    current_total_revenue = \
        Order.objects.filter(order_status=ORDER_STATUS[2][0]).aggregate(total_revenue=Sum('grand_total'))[
            'total_revenue'] or 0
    current_avg_order_price = \
        Order.objects.filter(order_status=ORDER_STATUS[2][0]).aggregate(avg_order_price=Avg('grand_total'))[
            'avg_order_price'] or 0
    previous_month_data = Order.objects.filter(created_at__range=(previous_month_start, previous_month_end)).filter(
        order_status=ORDER_STATUS[2][0]).aggregate(
        total_revenue=Sum('grand_total'), avg_order_price=Avg('grand_total')
    )
    current_month_data = Order.objects.filter(created_at__month=current_date.month).filter(
        order_status=ORDER_STATUS[2][0]).aggregate(
        total_revenue=Sum('grand_total'), avg_order_price=Avg('grand_total')
    )
    previous_month_total_revenue = previous_month_data['total_revenue'] or 0
    current_month_data = current_month_data['total_revenue'] or 0
    previous_month_avg_order_price = previous_month_data['avg_order_price'] or 0
    revenue_percentage_change = ((
                                         current_total_revenue - previous_month_total_revenue) / previous_month_total_revenue) * 100 if previous_month_total_revenue != 0 else 0
    avg_order_price_percentage_change = ((
                                                 current_avg_order_price - previous_month_avg_order_price) / previous_month_avg_order_price) * 100 if previous_month_avg_order_price != 0 else 0

    current_buses_count = Bus.objects.count()

    previous_month_buses_count = Bus.objects.filter(
        created_at__range=(previous_month_start, previous_month_end)).count()

    # Calculate the percentage change directly in the ORM query
    percentage_change = (
                                current_buses_count - previous_month_buses_count) * 100.0 / previous_month_buses_count if previous_month_buses_count != 0 else 0.0

    context = {
        "top_destination_locations": top_destination_locations,
        "top_pickup_locations": top_pickup_locations,
        "current_month_data": current_month_data,
        "previous_month_data": previous_month_total_revenue,
        "listOfLabels": listOfLabels,
        "listOfValues": listOfValues,
        "available_months": available_months,
        "available_years": available_years,
        'recent_20_orders': recent_20_orders,
        'current_orders_count': current_orders_count,
        'current_total_revenue': current_total_revenue,
        'current_avg_order_price': round(current_avg_order_price, 2),
        'revenue_percentage_change': round(revenue_percentage_change, 2),
        'avg_order_price_percentage_change': round(avg_order_price_percentage_change, 2),
        'buses': current_buses_count,
        'buses_percentage_change': round(percentage_change, 2)
    }
    print(context
          )
    return render(
        request, "crm/dashboard.html", context
    )


class BusesListView(ListView):
    model = Bus
    template_name = "crm/buses.html"
    context_object_name = "buses"
    ordering = ["id"]
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "Active")
        context["company"] = self.request.GET.get("company", "")
        context["name"] = self.request.GET.get("name", "")
        context["companies"] = Bus.objects.values_list("company_name", flat=True).distinct()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status", None)
        company = self.request.GET.get("company")
        name = self.request.GET.get("name")

        if status is not None:
            status = True if status == "Active" else False
            queryset = queryset.filter(is_available=status)
        if company:
            queryset = queryset.filter(company_name=company)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


def delete_bus(request, bus_id):
    if request.method == 'POST':
        bus = get_object_or_404(Bus, id=bus_id)
        bus.delete()
    return redirect('buses-list')


class BusesAddView(View):

    def get(self, request):
        form = BusForm()
        bus_charge_formset = BusChargeInlineForm(instance=Bus())
        return render(request, "crm/add-buses.html", {"form": form, "bus_charge_formset": bus_charge_formset})

    def post(self, request):
        bus_form = BusForm(request.POST, request.FILES)
        is_charge_valid = True
        form_charge = None
        bus_charge_formset = BusChargeInlineForm(instance=Bus())
        with transaction.atomic():
            if bus_form.is_valid():
                try:
                    bus = bus_form.save(commit=False)
                    bus.save()
                    data = request.POST
                    for i in range(len(BUS_CHARGES_SCALE)):
                        per_scale = data.get(f"bus_charges-{i}-per_scale_charges")
                        scale = data.get(f"bus_charges-{i}-scale")
                        if not scale:
                            continue
                        form_data = {"per_scale_charges": per_scale, "scale": scale, "bus": bus}
                        form_charge = BusChargeForm(form_data)

                        if form_charge.is_valid():
                            form_charge.save()
                        else:
                            is_charge_valid = False
                            break

                    if is_charge_valid:
                        return redirect("buses-list")
                except:
                    transaction.set_rollback(True)
            if not is_charge_valid and form_charge:
                transaction.set_rollback(True)
                add_form_errors_messages(form_charge, request)
            add_form_errors_messages(bus_form, request)
        return render(
            request,
            "crm/add-buses.html",
            {"form": bus_form, "bus_charge_formset": bus_charge_formset},
        )


class BusManageView(View):
    def get(self, request, bus_id):
        bus = Bus.objects.filter(id=bus_id).first()
        if not bus:
            messages.add_message(request, messages.ERROR, "Invalid Bus number")
            return redirect("buses-list")
        bus_form = BusForm(instance=bus)
        BusChargeFormSet = inlineformset_factory(Bus, BusCharges
                                                 , form=BusChargeForm, extra=0)
        bus_charge_formset = BusChargeFormSet(instance=bus)
        return render(request, "crm/add-buses.html",
                      {"form": bus_form, "bus": bus, "bus_charge_formset": bus_charge_formset})

    def post(self, request, bus_id):

        bus = Bus.objects.filter(id=bus_id).first()
        if not bus:
            messages.add_message(request, messages.ERROR, "Invalid Bus number")
            return redirect("buses-list")
        bus_form = BusForm(request.POST or None, request.FILES, instance=bus)
        is_charge_valid = True
        form_charge = None
        BusChargeFormSet = inlineformset_factory(Bus, BusCharges
                                                 , form=BusChargeForm, extra=0)
        bus_charge_formset = BusChargeFormSet(instance=bus)

        with transaction.atomic():
            if bus_form.is_valid():
                try:
                    bus_form.save()
                    data = request.POST
                    track_charges = []
                    for i in range(len(BUS_CHARGES_SCALE)):
                        id = data.get(f"bus_charges-{i}-id")
                        per_scale = data.get(f"bus_charges-{i}-per_scale_charges")
                        scale = data.get(f"bus_charges-{i}-scale")
                        if not scale:
                            continue
                        form_data = {"per_scale_charges": per_scale, "scale": scale, "bus": bus}
                        obj = None
                        if id:
                            obj = BusCharges.objects.filter(id=id).first()
                        form_charge = BusChargeForm(form_data, instance=obj)

                        if form_charge.is_valid():
                            saved_obj = form_charge.save()
                            track_charges.append(saved_obj.id)
                        else:
                            is_charge_valid = False
                            break
                        BusCharges.objects.filter(bus=bus).exclude(id__in=track_charges).delete()
                    if is_charge_valid:
                        return redirect("buses-list")
                except Exception as e:
                    transaction.set_rollback(True)
                    # Handle any exceptions that may occur during the save operation

            if not is_charge_valid and form_charge:
                transaction.set_rollback(True)
                add_form_errors_messages(form_charge, request)
            add_form_errors_messages(bus_form, request)
        return render(request, "crm/add-buses.html",
                      {"form": bus_form, "bus": bus, "bus_charge_formset": bus_charge_formset})

    def delete(self, request, bus_id):
        Bus.objects.filter(id=bus_id).delete()
        return redirect("buses")


class FaqAddView(View):

    def get(self, request):
        form = FaqForm()
        faq_category = FaqCategoryForm()
        return render(request, "crm/add-faqs.html", {"form": form, "faq_category": faq_category})

    def post(self, request):
        form = FaqForm(request.POST or None)
        faq_category = FaqCategoryForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("faq-list")
        return render(request, "crm/add-faqs.html", {"form": form, "form2": faq_category})


class FaqCategoryAddView(View):

    def post(self, request):
        form = FaqCategoryForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("add-faq")

        return render(request, "crm/add-faqs.html", {"form": form})


class FaqManageView(View):
    def get(self, request, faq_id):
        faq = Faqs.objects.get(id=faq_id)
        form = FaqForm(instance=faq)
        return render(request, "crm/add-faqs.html", {"form": form, "faq": faq})

    def post(self, request, faq_id):
        faq = Faqs.objects.get(id=faq_id)
        form = FaqForm(request.POST or None, instance=faq)
        if form.is_valid():
            form.save()
            return redirect("faq-list")
        return render(request, "crm/add-faqs.html", {"form": form, "faq": faq})

    def delete(self, request, faq_id):
        Faqs.objects.filter(id=faq_id).delete()
        return redirect("faqs")


class FaqsListView(ListView):
    model = Faqs
    template_name = "crm/faqs-list.html"
    context_object_name = "faqs"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = self.request.GET.get("type", "")
        context["unique_types"] = Faqs.objects.values_list("type__type", flat=True).distinct()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("type")

        if category:
            queryset = queryset.filter(type__type=category)
        return queryset


def delete_faq(request, faq_id):
    if request.method == 'POST':
        faq = get_object_or_404(Faqs, id=faq_id)
        faq.delete()
    return redirect('faq-list')


class UserListView(ListView):
    model = User
    template_name = "crm/user-list.html"
    context_object_name = "users"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status")
        context["user_info"] = self.request.GET.get("user_info", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status", "")
        user_info = self.request.GET.get("user_info")

        if status:
            status = True if status == "isStaff" else False
            queryset = queryset.filter(is_staff=status)
        if user_info:
            queryset = queryset.filter(Q(first_name__icontains=user_info) | Q(
                last_name__icontains=user_info) | Q(email__icontains=user_info) | Q(phone_number__icontains=user_info))

        return queryset


class OrderListView(ListView):
    model = Order
    template_name = "crm/order-list.html"
    context_object_name = "orders"
    ordering = ["id"]
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "Active")
        context["order_id"] = self.request.GET.get("order_id", "")
        context["user_info"] = self.request.GET.get("user_info", "")
        context["filter_by_date"] = self.request.GET.get("filter_by_date", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status", "")
        order_id = self.request.GET.get("order_id")
        user_info = self.request.GET.get("user_info")
        filter_by_date = self.request.GET.get("filter_by_date")

        if status:
            queryset = queryset.filter(order_status=status)
        if order_id:
            queryset = queryset.filter(Q(id=order_id) | Q(order_id=order_id))
        if user_info:
            queryset = queryset.filter(Q(first_name__icontains=user_info) | Q(first_name__icontains=user_info) | Q(
                last_name__icontains=user_info) | Q(email__icontains=user_info) | Q(phone_number__icontains=user_info))
        if filter_by_date is not None:
            current_date = timezone.now()
            if filter_by_date == "today":
                queryset = queryset.filter(created_at__date=current_date.date())
            if filter_by_date == "week":
                queryset = queryset.filter(created_at__week=current_date.isocalendar()[1])
            if filter_by_date == "month":
                queryset = queryset.filter(created_at__month=current_date.month)
            if filter_by_date == "year":
                queryset = queryset.filter(created_at__year=current_date.year)

        return queryset


class OrderDetailedVIew(DetailView):
    model = Order
    template_name = "crm/order_view.html"
    context_object_name = "order"


def add_user(request):
    return render(
        request, "crm/add-user.html"
    )


class CouponAddView(View):

    def get(self, request):
        form = CouponForm()
        return render(request, "crm/add-coupon.html", {"form": form})

    def post(self, request):
        form = CouponForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("coupon-list")
        return render(request, "crm/add-coupon.html", {"form": form})


class CouponManageView(View):
    def get(self, request, coupon_id):
        coupon = Coupons.objects.get(id=coupon_id)
        form = CouponForm(instance=coupon)
        return render(request, "crm/add-coupon.html", {"form": form, "coupon": coupon})

    def post(self, request, coupon_id):
        coupon = Coupons.objects.get(id=coupon_id)
        form = CouponForm(request.POST or None, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect("coupon-list")
        return render(request, "crm/add-coupon.html", {"form": form, "coupon": coupon})

    def delete(self, request, coupon_id):
        Coupons.objects.filter(id=coupon_id).delete()
        return redirect("coupons")


class CouponListView(ListView):
    model = Coupons
    template_name = "crm/coupon-list.html"
    context_object_name = "coupons"
    ordering = ["id"]
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "Active")
        context["scale"] = self.request.GET.get("scale""equal")
        context["code"] = self.request.GET.get("code", "")
        context["amount"] = self.request.GET.get("amount", "")

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status", None)
        scale = self.request.GET.get("scale")
        code = self.request.GET.get("code")
        amount = self.request.GET.get("amount", 0)
        print(status, scale, code, amount, '////////////////')
        try:
            amount = int(amount)
        except:
            amount = None
        if status is not None:
            status = True if status == "Active" else False
            current_date = timezone.now().date()
            queryset = queryset.filter(is_active=status, start_date__lte=current_date, end_date__gte=current_date)
        if scale is not None and amount is not None:
            if scale == "equal":
                queryset = queryset.filter(amount=amount)
            if scale == "less_then":
                queryset = queryset.filter(amount__lt=amount)
            if scale == "greater_then":
                queryset = queryset.filter(amount__gt=amount)
        if code:
            queryset = queryset.filter(code__icontains=code)
        return queryset


class TripListView(ListView):
    model = Trip
    template_name = "crm/trip-list.html"
    context_object_name = "trips"
    ordering = ["id"]
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["info"] = self.request.GET.get("info", "")
        context["status"] = self.request.GET.get("status", "Active")
        context["wayInfo"] = self.request.GET.get("wayInfo", "Active")
        context["filter_by_date"] = self.request.GET.get("filter_by_date", "")

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get("status", "")
        info = self.request.GET.get("info")
        wayInfo = self.request.GET.get("wayInfo")
        filter_by_date = self.request.GET.get("filter_by_date")

        if status:
            queryset = queryset.filter(trip_status=status)
        if wayInfo:
            wayInfo = True if wayInfo == "Is Two Way" else False
            queryset = queryset.filter(is_two_way_trip=wayInfo)
        if info:
            queryset = queryset.filter(Q(bus__name__icontains=info) | Q(user__email__icontains=info))
        if filter_by_date is not None:
            current_date = timezone.now()
            if filter_by_date == "today":
                queryset = queryset.filter(created_at__date=current_date.date())
            if filter_by_date == "week":
                queryset = queryset.filter(created_at__week=current_date.isocalendar()[1])
            if filter_by_date == "month":
                queryset = queryset.filter(created_at__month=current_date.month)
            if filter_by_date == "year":
                queryset = queryset.filter(created_at_year=current_date.year)

        return queryset


def delete_coupon(request, pk):
    if request.method == 'POST':
        cop = get_object_or_404(Coupons, id=pk)
        cop.delete()
    return redirect('coupon-list')


class PaymentListView(ListView):
    model = Payments
    template_name = "crm/payments.html"
    context_object_name = "payments"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Ostatus"] = self.request.GET.get("Ostatus", "")
        context["Pstatus"] = self.request.GET.get("Pstatus", "")
        context["info"] = self.request.GET.get("info", '')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        info = self.request.GET.get("info")
        Ostatus = self.request.GET.get("Ostatus")
        Pstatus = self.request.GET.get("Pstatus")

        if Ostatus:
            queryset = queryset.filter(order__order_status=Ostatus)
        if Pstatus:
            queryset = queryset.filter(payment_status=Pstatus)
        if info:
            queryset = queryset.filter(
                Q(order__order_id__icontains=info) | Q(payment_id__icontains=info) | Q(payment_gateway__icontains=info))
        return queryset


class RefundListView(ListView):
    model = Refund
    template_name = "crm/refunds.html"
    context_object_name = "refunds"
    ordering = ["id"]
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Ostatus"] = self.request.GET.get("Ostatus", "")
        context["Pstatus"] = self.request.GET.get("Pstatus", "")
        context["info"] = self.request.GET.get("info", '')
        return context


class RefundRequestView(ListView):
    model = Refund
    template_name = "crm/refunds-requests.html"
    context_object_name = "refunds"
    ordering = ["id"]
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().filter(refund_status=PAYMENT_STATUS[0][0])
        return queryset


class CityAddView(View):

    def get(self, request):
        form = CitiesForm()
        return render(request, "crm/add-city.html", {"form": form})

    def post(self, request):
        file = request.FILES.get("csv_file")

        if file:
            try:
                df = pd.read_csv(file)
                for index, row in df.iterrows():
                    try:
                        Cities.objects.get_or_create(city=row["city"], latitude=row["lat"], longitude=row["lng"])
                    except:
                        pass
                messages.add_message(request, messages.SUCCESS, "Cities imported")
                return redirect("city-list")
            except:
                messages.add_message(request, messages.ERROR, "Please Select a valid Cities files")
            return redirect("add-city")
        else:
            form = CitiesForm(request.POST or None)
            if form.is_valid():
                form.save()

                return redirect("city-list")
            else:
                return redirect("add-city")
        return render(request, "crm/add-city.html", {"form": form})


class CityListView(ListView):
    model = Cities
    template_name = "crm/city-list.html"
    context_object_name = "cities"
    ordering = ["id"]
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["city"] = self.request.GET.get("city", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        city = self.request.GET.get("city")

        if city:
            queryset = queryset.filter(city__icontains=city)
        return queryset


class CityManageView(View):
    def get(self, request, city_id):
        city = Cities.objects.get(id=city_id)
        form = CitiesForm(instance=city)
        return render(request, "crm/add-city.html", {"form": form, "city": city})

    def post(self, request, city_id):
        city = Cities.objects.get(id=city_id)
        form = CitiesForm(request.POST or None, instance=city)
        if form.is_valid():
            form.save()
            return redirect("city-list")

        return render(request, "crm/add-city.html", {"form": form, "city": city})

    def delete(self, request, city_id):
        Cities.objects.filter(id=city_id).delete()
        return redirect("cities")


def delete_city(request, pk):
    if request.method == 'POST':
        city = get_object_or_404(Cities, id=pk)
        city.delete()
    return redirect('city-list')


# Featured Trips Views handling

class FeaturedTripCreateView(View):
    def get(self, request):
        form = FeaturedTripsForm()
        stops_type = StopCharges.objects.all()
        return render(request, "crm/add-featured-trip.html", {"form": form, "stops_type": stops_type})

    def post(self, request):
        form = FeaturedTripsForm(request.POST or None)
        if form.is_valid():
            form.save()

            return redirect("featured-trip")
        return render(request, "crm/add-featured-trip.html", {"form": form})


class FeaturedTripListView(ListView):
    model = FeaturedTrips
    template_name = "crm/featured-trips.html"
    context_object_name = "featuredTrips"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip_info"] = self.request.GET.get("trip_info", "")
        context["rating"] = self.request.GET.get("rating", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        trip_info = self.request.GET.get("trip_info")
        rating = self.request.GET.get("rating")

        if trip_info:
            queryset = queryset.filter(bus__name__icontains=trip_info)
        if rating:
            rating_value = int(rating)
            min_rating = rating_value - 0.5
            max_rating = rating_value + 0.5
            queryset = queryset.filter(rating__gte=min_rating, rating__lt=max_rating)

        return queryset


class FeaturedTripManageView(View):
    def get(self, request, trip_id):
        trip = FeaturedTrips.objects.get(id=trip_id)
        form = FeaturedTripsForm(instance=trip)
        return render(request, "crm/add-featured-trip.html", {"form": form, "trip": trip})

    def post(self, request, trip_id):
        trip = FeaturedTrips.objects.get(id=trip_id)
        form = FeaturedTripsForm(request.POST or None, instance=trip)
        if form.is_valid():
            form.save()
            return redirect("featured-trip")
        return render(request, "crm/add-featured-trip.html", {"form": form, "trip": trip})

    def delete(self, request, trip_id):
        FeaturedTrips.objects.filter(id=trip_id).delete()
        return redirect("featured-trip")


# Stop Charges Views handling

class StopChargesListView(ListView):
    model = StopCharges
    template_name = "crm/stop-charge-list.html"
    context_object_name = "stopCharges"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.request.GET.get("title", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.GET.get("title")

        if title:
            queryset = queryset.filter(stop_title__icontains=title)
        return queryset


class StopChargesAddView(View):

    def get(self, request):
        form = StopChargesForm()
        return render(request, "crm/add-stop-charges.html", {"form": form})

    def post(self, request):
        form = StopChargesForm(request.POST or None)
        if form.is_valid():
            form.save()

            return redirect("stop-charges-list")
        return render(request, "crm/add-stop-charges.html", {"form": form})


class StopChargesManageView(View):
    def get(self, request, stop_id):
        stop = StopCharges.objects.get(id=stop_id)
        form = StopChargesForm(instance=stop)
        return render(request, "crm/add-stop-charges.html", {"form": form, "stop": stop})

    def post(self, request, stop_id):
        stop = StopCharges.objects.get(id=stop_id)
        form = StopChargesForm(request.POST or None, instance=stop)
        if form.is_valid():
            form.save()
            return redirect("stop-charges-list")
        return render(request, "crm/add-stop-charges.html", {"form": form, "stop": stop})

    def delete(self, request, stop_id):
        StopCharges.objects.filter(id=stop_id).delete()
        return redirect("stop-charges-list")


def delete_stop_charges(request, pk):
    if request.method == 'POST':
        stop = get_object_or_404(StopCharges, id=pk)
        stop.delete()
    return redirect('stop-charges-list')


# License Views handling

class LicenseListView(ListView):
    model = License
    template_name = "crm/license-list.html"
    context_object_name = "licenses"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Lname"] = self.request.GET.get("Lname", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        Lname = self.request.GET.get("Lname")

        if Lname:
            queryset = queryset.filter(license_name__icontains=Lname)
        return queryset


class LicenseAddView(View):

    def get(self, request):
        form = LicenseForm()
        return render(request, "crm/add-license.html", {"form": form})

    def post(self, request):
        form = LicenseForm(request.POST or None)
        if form.is_valid():
            form.save()

            return redirect("license-list")
        return render(request, "crm/add-license.html", {"form": form})


class LicenseManageView(View):
    def get(self, request, license_id):
        license = License.objects.get(id=license_id)
        form = LicenseForm(instance=license)
        return render(request, "crm/add-license.html", {"form": form, "license": license})

    def post(self, request, license_id):
        license = License.objects.get(id=license_id)
        form = LicenseForm(request.POST or None, instance=license)
        if form.is_valid():
            form.save()
            return redirect("license-list")
        return render(request, "crm/add-license.html", {"form": form, "license": license})

    def delete(self, request, license_id):
        License.objects.filter(id=license_id).delete()
        return redirect("license-list")


def delete_license(request, pk):
    if request.method == 'POST':
        license = get_object_or_404(License, id=pk)
        license.delete()
    return redirect('license-list')


# Insurance Views handling

class InsuranceListView(ListView):
    model = Insurance
    template_name = "crm/insurances-list.html"
    context_object_name = "insurances"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Iname"] = self.request.GET.get("Iname", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        Iname = self.request.GET.get("Iname")

        if Iname:
            queryset = queryset.filter(name__icontains=Iname)
        return queryset


class InsuranceAddView(View):

    def get(self, request):
        form = InsuranceForm()
        return render(request, "crm/add-insurance.html", {"form": form})

    def post(self, request):
        form = InsuranceForm(request.POST or None)
        if form.is_valid():
            form.save()

            return redirect("insurance-list")
        return render(request, "crm/add-insurance.html", {"form": form})


class InsuranceManageView(View):
    def get(self, request, insurance_id):
        insurance = Insurance.objects.get(id=insurance_id)
        form = InsuranceForm(instance=insurance)
        return render(request, "crm/add-insurance.html", {"form": form, "insurance": insurance})

    def post(self, request, insurance_id):
        insurance = Insurance.objects.get(id=insurance_id)
        form = InsuranceForm(request.POST or None, instance=insurance)
        if form.is_valid():
            form.save()
            return redirect("insurance-list")
        return render(request, "crm/add-insurance.html", {"form": form, "insurance": insurance})

    def delete(self, request, insurance_id):
        Insurance.objects.filter(id=insurance_id).delete()
        return redirect("insurance-list")


def delete_insurance(request, pk):
    if request.method == 'POST':
        insurance = get_object_or_404(Insurance, id=pk)
        insurance.delete()
    return redirect('insurance-list')


# Trip category Views handling

class TripCategoryListView(ListView):
    model = TripCategory
    template_name = "crm/trip-category-list.html"
    context_object_name = "tripCategories"
    ordering = ["id"]
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.request.GET.get("trip", "")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        trip = self.request.GET.get("trip")

        if trip:
            queryset = queryset.filter(name__icontains=trip)
        return queryset


class TripCategoryAddView(View):

    def get(self, request):
        form = TripCategoryForm()
        return render(request, "crm/add-trip-category.html", {"form": form})

    def post(self, request):
        form = TripCategoryForm(request.POST or None)
        if form.is_valid():
            form.save()

            return redirect("trip-category-list")
        return render(request, "crm/add-trip-category.html", {"form": form})


class TripCategoryManageView(View):
    def get(self, request, trip_category_id):
        trip_category = TripCategory.objects.get(id=trip_category_id)
        form = TripCategoryForm(instance=trip_category)
        return render(request, "crm/add-trip-category.html", {"form": form, "trip_category": trip_category})

    def post(self, request, trip_category_id):
        trip_category = TripCategory.objects.get(id=trip_category_id)
        form = TripCategoryForm(request.POST or None, instance=trip_category)
        if form.is_valid():
            form.save()
            return redirect("trip-category-list")
        return render(request, "crm/add-trip-category.html", {"form": form, "trip_category": trip_category})

    def delete(self, request, trip_category_id):
        TripCategory.objects.filter(id=trip_category_id).delete()
        return redirect("trip-category-list")


def delete_trip_category(request, pk):
    if request.method == 'POST':
        trip_category = get_object_or_404(TripCategory, id=pk)
        trip_category.delete()
    return redirect('trip-category-list')


class UpdateOrderCashPayment(View):
    def post(self, request):
        order_id = request.POST.get("order_id")
        payment_paid = request.POST.get("payment_amount", "0.0")
        try:
            float(payment_paid)
        except:
            messages.add_message(request, messages.ERROR, _("Invalid amount entered. Please enter a valid number."))
            return redirect("orders")
        if not order_id:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("orders")
        if not payment_paid:
            messages.add_message(request, messages.ERROR, _("Payment required"))
            return redirect("orders")
        order = Order.objects.filter(id=order_id, order_status=ORDER_STATUS[1][0]).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("orders")
        payment = order.order_payments.filter(payment_status=PAYMENT_STATUS[1][0],
                                              payment_gateway=PAYMENT_GATEWAYS[1][0]).first()
        if not payment:
            messages.add_message(request, messages.ERROR, _("Invalid Payment details"))
            return redirect("orders")
        payment_paid = Decimal(payment_paid)
        discount = 0
        if payment.order.sub_total >= payment_paid:
            discount = payment.order.sub_total - payment_paid
        order.paid_amount = payment_paid
        order.order_status = ORDER_STATUS[2][0]
        payment.paid_amount = payment_paid
        payment.discount = discount
        payment.payment_id = str(uuid.uuid4())
        payment.payment_status = PAYMENT_STATUS[2][0]
        payment.save()
        order.save()
        bus = order.trip.bus
        bus.is_available = False
        bus.bus_status = BUS_STATUS[2][0]
        bus.save()
        user = order.trip.user
        password = None
        if user.is_order_user:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user.set_password(password)
            user.is_order_user = False
            user.save()
        send_order_payment_confirmation.delay(order.id, user.id, password)
        create_xero_invoice.delay(order.id)
        messages.add_message(request, messages.SUCCESS, _("Order has been confirmed"))
        return redirect("orders")


class MarkCompleted(View):
    def get(self, request, pk):
        order = Order.objects.filter(id=pk, order_status=ORDER_STATUS[2][0]).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("orders")
        order.order_status = ORDER_STATUS[5][0]
        order.save()
        bus = order.trip.bus
        bus.is_available = True
        trip = order.trip
        trip.bus_returned_date = timezone.now()
        trip.save()
        bus.save()
        messages.add_message(request, messages.SUCCESS, _("Order has been Completed"))
        return redirect("orders")


class MarkRejected(View):
    def get(self, request, pk):
        order = Order.objects.filter(Q(order_status=ORDER_STATUS[0][0]) | Q(order_status=ORDER_STATUS[1][0]),
                                     id=pk).first()
        if not order:
            messages.add_message(request, messages.ERROR, _("Invalid Order number"))
            return redirect("orders")
        order.order_status = ORDER_STATUS[3][0]
        order.save()
        bus = order.trip.bus
        bus.is_available = True
        trip = order.trip
        trip.trip_status = TRIP_STATUS[3][0]
        trip.save()
        bus.save()
        payment = order.order_payments.all()
        for pay in payment:
            pay.payment_status = PAYMENT_STATUS[3][0]
            pay.save()
        messages.add_message(request, messages.INFO, _("Order has been Rejected"))
        return redirect("orders")


class XeroView(View):
    def get(self, request):
        xero = Xero.objects.first()
        organizations = []
        accounts = []

        if xero and xero.access_token and (not xero.tenant_id):
            client = XeroClient(xero.access_token)
            organizations = client.get_connections()
        if xero and xero.access_token and not xero.account_id and xero.tenant_id:
            client = XeroClient(xero.access_token)
            accounts = client.get_accounts(xero.tenant_id).get("Accounts", [])
        return render(request, "crm/xero.html", {"xero": xero, "organizations": organizations, "accounts": accounts})

    def post(self, request):
        xero = Xero.objects.first()
        if not xero:
            messages.add_message(request, messages.ERROR, "Please connect your xero  account")
            return redirect("xero")
        account = request.POST.get("account", "")
        organization = request.POST.get("organization")
        if account:
            account_id = account.split("___")[0]
            account_name = account.split("___")[1]
            xero.account_id = account_id
            xero.account_name = account_name
        if organization:
            org_id = organization.split("___")[0]
            org_name = organization.split("___")[1]
            xero.tenant_id = org_id
            xero.organization = org_name
        xero.save()
        return redirect("xero")


class XeroViewLogin(View):

    def get(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            client = XeroClient()
            Xero.objects.get_or_create(admin_user=request.user)
            token, _ = Token.objects.get_or_create(user=request.user)
            state = client.encrypt_token(token)
            url = client.get_login_url(state)
            return redirect(url)
        else:
            return redirect("/")


class XeroViewLogout(View):
    def get(self, request):
        xero = Xero.objects.first()
        if not xero:
            messages.add_message(request, messages.ERROR, "Please connect your xero  account")
            return redirect("xero")
        xero.delete()
        messages.add_message(request, messages.INFO, "Xero disconnected")
        return redirect("xero")

class GoogleCalendarView(View):
    def get(self, request):
        google = GoogleAuth.objects.first()
        return render(request, "crm/google.html", {"google": google})

class GoogleViewLogin(View):

    def get(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            client = GoogleAPI()
            GoogleAuth.objects.get_or_create(user=request.user)
            url = client.get_login_url(request.user)
            return redirect(url)
        else:
            return redirect("/")


class GoogleViewLogout(View):
    def get(self, request):
        google = GoogleAuth.objects.first()
        if not google:
            messages.add_message(request, messages.ERROR, "Please connect your google account")
            return redirect("crm-google")
        google.delete()
        messages.add_message(request, messages.INFO, "Google disconnected")
        return redirect("crm-google")


