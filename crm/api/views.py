import json
import uuid
from decimal import Decimal

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, F
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.viewsets import ViewSet
from datetime import datetime, timedelta
from booking.models import Order
from booking.payments.stripe import StripeClient
import calendar
from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from booking.models import *


def earnings_chart(request):
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    # Apply filters
    orders = Order.objects.all()

    if selected_month:
        orders = orders.filter(created_at__month=selected_month)

    if selected_year:
        orders = orders.filter(created_at__year=selected_year)
    earnings_data = calculate_earnings(orders, selected_year, selected_month)

    # Prepare data for the line chart
    labels = list(earnings_data.keys())
    values = list(earnings_data.values())

    context = {
        'labels': labels,
        'values': values,
    }

    return JsonResponse(context)


from datetime import datetime, timedelta


def calculate_earnings(orders, selected_year, selected_month):
    earnings_data = {}
    last_day = calendar.monthrange(selected_year, selected_month)[1]
    date_range = [datetime(selected_year, selected_month, day) for day in range(1, last_day + 1)]
    for date in date_range:
        date_str = date.strftime('%d-%m-%Y')
        if date_str not in earnings_data:
            earnings_data[date_str] = 0.0
    for order in orders:
        date_str = order.created_at.strftime('%d-%m-%Y')
        if date_str in earnings_data:
            earnings_data[date_str] += float(order.grand_total)
        else:
            earnings_data[date_str] = float(order.grand_total)

    # Calculate the last day of the selected month

    # Create a date range for the entire month

    # Fill in earnings data for each day in the date range
    for date in date_range:
        date_str = date.strftime('%d-%m-%Y')
        if date_str not in earnings_data:
            earnings_data[date_str] = 0.0

    return earnings_data


@csrf_exempt
def delete_bus_image(request, pk):
    BusImages.objects.filter(id=pk).delete()
    return JsonResponse({"message": "Deleted"}, status=200)


@csrf_exempt
def refund_request_view(request):
    data = request.POST
    action = data.get("action", "").lower()

    refund_id = data.get("refund_id")
    if not action or not refund_id:
        return JsonResponse({"message": "Something went  wrong", "status": 400})
    refund = Refund.objects.filter(id=refund_id).first()
    order = refund.order
    if not refund:
        return JsonResponse({"message": "Unable to change  the status", "status": 400})
    if action == "approve":
        client = StripeClient()
        payment = refund.order.order_payments.filter(payment_gateway=PAYMENT_GATEWAYS[0][0]).first()
        if payment:
            res, code = client.refund(payment.payment_id)
            if code != 200:
                refund.refund_status = PAYMENT_STATUS[2][0]
                refund.save()
                refund.refund_id = res.get("id")
                order.order_status = ORDER_STATUS[6][0]
                order.save()
        else:
            refund.refund_status = PAYMENT_STATUS[2][0]
            refund.save()
            refund.refund_id = f"{uuid.uuid4()}"
            order.order_status = ORDER_STATUS[6][0]
            order.save()
    elif action == "reject":
        refund.refund_status = PAYMENT_STATUS[3][0]
        refund.save()
        order.order_status = ORDER_STATUS[2][0]
        order.save()
    return JsonResponse({"message": "Ok", "status": 200})


@csrf_exempt
def save_featured_trip_details(request):
    data = request.POST
    stops = data.get("stops", [])
    pickup_lat = data.get("pickup_lat")
    pickup = data.get("pickup")
    destination = data.get("destination")
    pickup_long = data.get("pickup_long")
    destination_lat = data.get("destination_lat")
    destination_long = data.get("destination_long")
    number_children = data.get("id_number_children")
    number_adults = data.get("id_number_adults")
    weight_of_luggage = data.get("id_weight_of_luggage")
    total_time_in_mint = data.get("total_time_in_mint")
    total_distance_in_number = data.get("total_distance_in_number")
    if total_distance_in_number == "NaN":
        total_distance_in_number = 0
    bus_id = data.get("bus")
    price = data.get("price")
    discount_price = data.get("discount_price")
    rating = int(data.get("rating", 5))
    if rating > 5:
        rating = 5
    bus = Bus.objects.filter(id=bus_id).first()
    bus_charges = BusCharges.objects.filter(bus=bus,scale="Hour").first()
    if not bus_charges:
        return JsonResponse({"message": "Not able to create trip due  to incomplete info of the bus"})
    trip_instance, created = Trip.objects.get_or_create(
        bus=bus,
        scale=bus_charges.scale,
        per_scale_charges=bus_charges.per_scale_charges,
        number_children=number_children,
        number_adults=number_adults,
        weight_of_luggage=weight_of_luggage,
        trip_type=TRIP_TYPE[0][0]
    )
    route = Route.objects.create(
        trip=trip_instance,
        route_type=ROUTE_TYPES[0][0],
        departure_latitude=pickup_lat,
        departure_longitude=pickup_long,
        departure_city=pickup,
        destination_latitude=destination_lat,
        destination_longitude=destination_long,
        destination_city=destination,
        total_distance=total_distance_in_number,
        total_distance_in_km=f"{total_distance_in_number} km",
        estimated_time=total_time_in_mint,

    )
    stops = json.loads(stops)
    for stop in stops:
        stop_charge = StopCharges.objects.filter(id=stop['breakFor']).first()
        numOfMinutes = stop.get('numOfMinutes')
        if not numOfMinutes:
            numOfMinutes = 0
        stop_instance, created = Stops.objects.get_or_create(
            location=stop['location'],
            latitude=stop['latitude'],
            longitude=stop['longitude'],
            stop_charge=stop_charge,
            minutes=numOfMinutes,
        )
        route.bus_stops.add(stop_instance)
    try:
        featured = FeaturedTrips.objects.create(
            bus=bus,
            trip=trip_instance,
            price=Decimal(price),
            discount_price=Decimal(discount_price),
            rating=rating,
        )
    except:
        return JsonResponse({"error": "Something went wrong while creating featured trips"}, status=400)
    return JsonResponse({"message": "Featured Trip configured"})


from datetime import datetime, timedelta
from django.http import JsonResponse


@csrf_exempt
def get_calendar_events(request):
    from crm.Integrations.GoogleAPI import GoogleAPI
    from crm.models import GoogleAuth

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        start_date = (end_date - timedelta(days=30)).strftime("%Y-%m-%d")

    if not end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()
        end_date = (start_date + timedelta(days=30)).strftime("%Y-%m-%d")

    google = GoogleAuth.objects.first()
    events = GoogleAPI().get_gmail_events(google, start_date, end_date)
    return JsonResponse({"events": events})
