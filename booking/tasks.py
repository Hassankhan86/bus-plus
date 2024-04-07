# tasks.py
from decimal import Decimal

from celery import shared_task
from datetime import timedelta, datetime

from django.template.loader import get_template
from django.utils import timezone
from booking.CONSTANT import *
from booking.api.xero import XeroClient
from booking.models import Order, User, Refund, Payments, Xero, TripInsurance
from booking.utils import send_email
from booking.utils import parse_str_date_time
import pytz
from django.conf import settings


@shared_task
def cancel_unpaid_reservations(order_id):
    try:
        order = Order.objects.get(id=order_id, order_status=ORDER_STATUS[0][0])
        paid_payments = order.order_payments.filter(payment_id__isnull=False,
                                                    payment_status=PAYMENT_STATUS[2][0]).first()
        if paid_payments:
            bus = order.trip.bus
            bus.is_available = False
            bus.bus_status = BUS_STATUS[2][0]
            bus.save()
        else:
            bus = order.trip.bus
            bus.is_available = True
            bus.bus_status = BUS_STATUS[0][0]
            bus.save()
            for pay in order.order_payments.all():
                pay.payment_status = PAYMENT_STATUS[4][0]
                pay.save()
            order.order_status = ORDER_STATUS[4][0]
            order.save()
            send_email("Trip Reservation Status", "Your trip reservation bas been  cancelled due to payment",
                       order.email)
    except Order.DoesNotExist:
        pass


@shared_task
def update_completed_orders():
    today = timezone.now().astimezone(pytz.utc).replace(tzinfo=None)
    confirmed_orders = Order.objects.filter(order_status=ORDER_STATUS[2][0])
    for order in confirmed_orders:
        try:
            route = order.trip.routes.all().last()
            if route and parse_str_date_time(route.drop_off_date, route.drop_off_time, 30) <= today:
                paid_payment = order.order_payments.filter(payment_id__isnull=False,
                                                           payment_status=PAYMENT_STATUS[2][0]).first()
                if paid_payment:
                    order.order_status = ORDER_STATUS[5][0]
                    order.save()
                    bus = order.trip.bus
                    bus.is_available = True
                    bus.bus_status = BUS_STATUS[0][0]
                    bus.save()
                else:
                    pass
        except:
            pass


@shared_task
def send_order_confirmation(order_id, user_id):
    order = Order.objects.filter(id=order_id).first()
    user = User.objects.filter(id=user_id).first()
    if not user or not order:
        return
    template = get_template('render-templates/order-confirmation.html').render({
        'order': order
    })

    subject = 'Order Confirmation'
    # message = f'Hi {user.first_name if user.first_name else user.email},\n\nThank you for your order. Here are the
    # details:\n\nOrder ID: {order.order_id}\nSub Total: {order.sub_total}\nDiscount: {order.discount}\nGrand Total:
    # {order.grand_total}\n\nPlease make the payment as soon as possible; otherwise, your trip will be
    # cancelled.\n\nPlease let us know if you have any questions.\n\nBest Regards,\nThe Buses Plus Team'
    recipient_list = [user.email]
    send_email(subject, "", recipient_list, html_message=template)


@shared_task
def send_order_payment_confirmation(order_id, user_id, password=None):
    order = Order.objects.filter(id=order_id).first()
    user = User.objects.filter(id=user_id).first()
    if not user or not order:
        return
    subject = 'Order Payment Confirmation'
    message = f'Hi {user.first_name if user.first_name else user.email},\n\nThank you for your payment. Here are the payment details:\n\nOrder ID: {order.order_id}\nSub Total: {order.sub_total}\nDiscount: {order.discount}\nGrand Total: {order.grand_total}\n\n{"Here is Your password:" + password if password else ""}\n\nPlease let us know if you have any questions.\n\nBest Regards,\nThe Buses Plus Team'
    recipient_list = [user.email]
    send_email(subject, message, recipient_list)


@shared_task
def send_refund_email_init(refund_id):
    refund = Refund.objects.filter(id=refund_id).first()
    if not refund:
        return
    subject = "Refund Request Initiated"
    message = f"Your refund request has been initiated\n\nHere is your refund request id: {refund.id}\n\nThank you,\n\nBuses Plus"
    recipient_list = [refund.order.email]
    send_email(subject, message, recipient_list)


@shared_task
def send_refund_email(refund_id):
    refund = Refund.objects.filter(id=refund_id).first()

    if not refund:
        return

    subject = "Refund Request Status"
    paid = refund.order.order_payments.filter(payment_status=PAYMENT_STATUS[2][0]).first()
    if not paid:
        return
    if paid.payment_gateway != PAYMENT_GATEWAYS[0][0]:
        payment_info = "Collect your cash from Buses Plus office."
    else:
        payment_info = "Your refund payment will be processed within 1-3 days."

    if refund.refund_status == PAYMENT_STATUS[3][0]:
        status = "rejected"
    else:
        status = f"approved, {payment_info}"

    message = f"Your refund request has been {status}\n\nThank you,\n\nBuses Plus"

    recipient_list = [refund.order.email]
    send_email(subject, message, recipient_list)


@shared_task
def contactus_email(subject, message):
    recipient_list = settings.ADMIN_USERS
    send_email(subject, message, recipient_list)
    return True


@shared_task
def create_xero_invoice(order_id):
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return
    xero = Xero.objects.first()
    if not xero or not xero.tenant_id:
        return
    lines_items = []
    if order.trip.trip_type == TRIP_TYPE[2][0]:
        lines_items.append(
            {
                "Description": "Self  Drive",
                "Quantity": 1,
                "UnitAmount": str(order.trip.self_drive_price()),
                "AccountCode": "200"
            }
        )
    else:
        routes = order.trip.routes.all()
        for route in routes:
            route_item = {

                "Description": route.route_type,
                "Quantity": 1,
                "UnitAmount": str(round((Decimal(route.total_distance_in_km) * order.trip.per_scale_charges), 2)),
                "AccountCode": "200"
            }
            lines_items.append(route_item)
            for stop in route.bus_stops.all():
                stop_item = {

                    "Description": f"{stop.minutes} Break for `{stop.stop_charge.stop_title}` at {stop.location}",
                    "Quantity": 1,
                    "UnitAmount": stop.stop_charges(),
                    "AccountCode": "200"
                }
                lines_items.append((stop_item))
    trip_insurances = order.trip.trip_insurances.all()
    for insurance  in trip_insurances:
        for ins in insurance.insurance.all():
            lines_items.append(
                {
                    "Description": f"Insurance: {ins.name}",
                    "Quantity": 1,
                    "UnitAmount": str(ins.premium),
                    "AccountCode": "200"
                }
            )
    tax_amount = {
        "Description": "Tax (3%)",
        "Quantity": 1,
        "UnitAmount": order.trip.get_trip_tax(),
        "AccountCode": "200"
    }
    platform_charges = {
        "Description": "Platform charges",
        "Quantity": 1,
        "UnitAmount": order.trip.get_service_charge(),
        "AccountCode": "200"
    }
    lines_items.append(tax_amount)
    lines_items.append(platform_charges)
    invoice_data = {
        "Type": "ACCREC",
        "Contact": {
            "Name": f"{order.first_name} {order.last_name}",
            "EmailAddress": order.email,
            "Phones": [
                {
                    "PhoneType": "MOBILE",
                    "PhoneNumber": order.phone_number if order.phone_number else "",
                    "PhoneAreaCode": "",
                    "PhoneCountryCode": ""
                }
            ]
        },
        "Date": str(order.created_at),
        "DueDate": str(order.get_order_date()),
        "Status": "AUTHORISED",
        "TaxType": "Sales Tax",
        "CurrencyCode": "AUD",
        "InvoiceNumber": f"{order.order_id}",
        "Reference": f"Buses Plus Order No:{order.id}",
        "LineItems": lines_items
    }
    client = XeroClient(xero.access_token)
    res = client.create_invoice(xero.tenant_id, invoice_data)
    invoices = res.get("Invoices", [])

    if len(invoices) > 0:
        make_xero_payment(invoices[0]["InvoiceID"], order_id)


def make_xero_payment(invoice_id, order_id):
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return
    xero = Xero.objects.first()
    if not xero or not xero.account_id:
        return
    payment = order.get_payment_obj()
    payment_gateway = "CreditCard"
    if payment:
        payment_gateway = order.get_payment_obj().payment_gateway

    data = {
        "Invoice": {
            "InvoiceID": invoice_id
        },
        "Account": {
            "AccountID": xero.account_id
        },
        "Amount": str(order.grand_total),
        "Date": str(order.get_order_date()),
        "PaymentType": payment_gateway,
        "Reference": f"Payment for Invoice #{order.order_id}"
    }
    client = XeroClient(xero.access_token)
    res = client.make_payment(xero.tenant_id, data)
    print(res)
