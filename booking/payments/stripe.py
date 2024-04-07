import random
import string
import requests
import stripe
from decimal import Decimal
from django.conf import settings
from booking.models import Payments, Order
from booking.CONSTANT import *
from booking.tasks import send_order_payment_confirmation, create_xero_invoice


def decamelize_with_underscores(s):
    # Replace dots with underscores and convert camel case to snake case
    s = s.replace('.', '_')
    return ''.join(['_' + c.lower() if c.isupper() else c for c in s]).lstrip('_')


class StripeClient:
    def __init__(self) -> None:
        self.api_key = settings.STRIPE_PRIVATE_KEY
        self.public_key = settings.STRIPE_PUBLIC_KEY
        stripe.api_key = self.api_key
        self.endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
        self.api="https://api.stripe.com/v1/"

    def create_payment_intent(self, amount):
        intent = stripe.PaymentIntent.create(
            amount=int(amount)*100,
            currency='aud',
            payment_method_types=['card'],
            payment_method_options={
                'card': {
                    'request_three_d_secure': 'any',
                },
            }
        )

        return intent.get('client_secret')
    def  post(self,data):
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        end_point = f"{self.api}refunds"
        res = requests.post(end_point, data=data, headers=headers)
        response_data = {}
        try:
            response_data = res.json()
        except:
            response_data["res"] = res.text
        return response_data, res.status_code

    def refund(self, charge_id):
        data = {
            "charge": charge_id
        }
        return  self.post(data)


    def webhook(self, data, payload, sig_header):
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            raise e
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise e

        event_type = event.get("type", "")
        function = function = f'handle_{decamelize_with_underscores(event_type)}'
        try:
            return getattr(self, function)(data)
        except Exception as ex:
            print(f"Webhook event {function} is not yet supported")
            return False

    def handle_charge_succeeded(self, data):

        _object = data.get("data", {}).get("object", {})
        payment_intent = _object.get("payment_intent")
        amount_captured = Decimal(_object.get("amount_captured", 0.0))
        if amount_captured:
            amount_captured = amount_captured / 100
        charge_id = _object.get("id")
        status = _object.get("paid", False)
        payment = Payments.objects.filter(payment_intent_id=payment_intent).first()
        if not payment:
            return False
        payment.payment_id = charge_id
        payment.payment_gateway = PAYMENT_GATEWAYS[0][0]
        payment.paid_amount=amount_captured

        order = payment.order
        order.paid_amount = amount_captured
        if status:
            payment.payment_status = PAYMENT_STATUS[2][0]
            payment.paid_amount = (amount_captured)
            order.order_status = ORDER_STATUS[2][0]
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

            send_order_payment_confirmation.delay(order.id,user.id, password)
            create_xero_invoice.delay(order.id)
        else:
            payment.payment_status = PAYMENT_STATUS[4][0]
            order.order_status = ORDER_STATUS[4][0]
            bus = order.trip.bus
            bus.is_available = True
            bus.bus_status = BUS_STATUS[0][0]
            bus.save()
        order.save()
        payment.save()
        return True