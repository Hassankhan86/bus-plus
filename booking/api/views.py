from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt

from booking.api.xero import XeroClient
from booking.models import *
from booking.serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.utils import timezone
from booking.payments.stripe import StripeClient
from booking.utils import serializer_errors_list, convert_to_timedelta, add_stop_time_in_route
from django.conf import settings
from django.http import JsonResponse
import random
import string
from django.shortcuts import redirect
from rest_framework.authtoken.models import Token

from crm.Integrations.GoogleAPI import GoogleAPI
from datetime import datetime
from crm.models import GoogleAuth


class CitiesView(APIView):
    permission_classes = [AllowAny]
    queryset = Cities.objects.all()

    def get(self, request):
        data = CitiesSerializers(Cities.objects.all(), many=True).data
        return Response(data)


class InsurancesView(APIView):
    permission_classes = [AllowAny]
    queryset = Insurance.objects.all()

    def get(self, request, pk):
        ins = Insurance.objects.filter(id=pk).first()
        if not ins:
            return Response({"message": "Invalid insurance selection"})
        data = InsurancesSerializer(ins).data
        return Response(data)


class TripeCreateView(APIView):
    permission_classes = [AllowAny]
    queryset = Trip.objects.all()
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = TripCreateSerializer(data=data)
        if serializer.is_valid():
            trip = serializer.save()
            return Response(TripSerializer(trip).data)
        else:
            return Response(serializer_errors_list(serializer), status=status.HTTP_400_BAD_REQUEST)


class StopsListView(APIView):
    permission_classes = [AllowAny]
    queryset = Stops.objects.all()

    def post(self, request):
        data = request.data
        stops = data.get("stops", [])
        stops_list = []
        trip = Trip.objects.get(id=data.get("trip"))
        for stop in stops:
            numOfMinutes = stop.get("numOfMinutes", 0)
            routeType = stop.get("routeType")
            route = trip.routes.filter(route_type=routeType).first()
            if numOfMinutes and routeType:
                stop_charge = StopCharges.objects.get(id=stop.get("breakFor"))
                st, _ = Stops.objects.update_or_create(route_type=routeType, location=stop.get("location"),
                                                       stop_charge=stop_charge,
                                                       defaults={"minutes": stop.get("numOfMinutes", 0),
                                                                 "latitude": stop.get("latitude"),
                                                                 "longitude": stop.get("longitude")})

                route.bus_stops.add(st)
                stops_list.append(st.id)
        route_stops_ids = trip.routes.values_list('bus_stops__id', flat=True)
        stops_to_remove = set(route_stops_ids) - set(stops_list)
        Stops.objects.filter(id__in=stops_to_remove).delete()
        trip_route = trip.routes.all().first()

        if trip_route:
            # Calculate the total stop time in minutes using a queryset
            total_stop_time_query = trip_route.bus_stops.aggregate(total_time=Sum('minutes'))
            total_stop_time_minutes = total_stop_time_query['total_time'] or 0
            drop_off_date, drop_off_time_str = add_stop_time_in_route(trip_route.pickup_time, trip_route.pickup_date,
                                                                      total_stop_time_minutes,
                                                                      trip_route.estimated_time)
            trip_route.drop_off_time = drop_off_time_str
            trip_route.drop_off_date = drop_off_date
            trip_route.save()
        return Response(TripSerializer(trip).data)


class CheckCouponView(APIView):
    permission_classes = [AllowAny]
    queryset = Coupons.objects.all()

    def post(self, request):
        data = request.data
        trip_id = data.get("trip")
        code = data.get("coupon")
        trip = Trip.objects.filter(id=trip_id).first()

        if not trip:
            return Response({"message": "Invalid trip information", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        if not code:
            return Response({"message": "Coupon Code is required", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        coupon = Coupons.objects.filter(code=code, is_active=True).first()
        if not coupon:
            return Response({"message": f"Invalid Coupon Code", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        current_date = timezone.now()
        if coupon.start_date > current_date:
            return Response({"message": f"This Coupon is'nt started, will start from {coupon.start_date.date()}",
                             status: status.HTTP_202_ACCEPTED}, status=status.HTTP_400_BAD_REQUEST)
        if coupon.end_date < current_date:
            return Response({"message": f"Coupon is expired", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        if coupon.minimum_amount > trip.get_trip_charges():
            return Response(
                {"message": f"Coupon doesn't meet  the requirements", "status": status.HTTP_400_BAD_REQUEST},
                status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"Coupon will applied on booking confirmation, you will save ${coupon.amount}",
                         "status": status.HTTP_200_OK}, status=status.HTTP_200_OK)


class StripView(ViewSet):
    queryset = Order.objects.all()
    permission_classes = [AllowAny]

    @csrf_exempt
    @action(methods=["POST"], detail=False, url_name="stripe-create-intent", url_path="stripe-create-intent",
            permission_classes=[AllowAny])
    def stripe_create_intent(self, request):
        data = request.data
        order_id = data.get("order_id")
        order = Order.objects.filter(order_id=order_id).first()
        if not order:
            return Response({"message": "Invalid Order number", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)

        payment, _ = Payments.objects.get_or_create(order=order)
        if payment and payment.payment_id:
            return Response({"message": "Order already Paid", "status": status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        if not payment.payment_intent_id:
            try:
                client = StripeClient()
                intent_secret = client.create_payment_intent(order.grand_total)
                if not intent_secret:
                    return Response({"message": "We are unable to process card  payment now please select cash pyament "
                                                "method", "status": status.HTTP_400_BAD_REQUEST},
                                    status=status.HTTP_400_BAD_REQUEST)
                payment.payment_intent_id = str(intent_secret.split("_secret_")[0]).strip()
                payment.payment_intent_secret = intent_secret
                payment.save()
            except:
                return Response({"message": "We are unable to process card  payment now please select cash pyament "
                                            "method", "status": status.HTTP_400_BAD_REQUEST},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response({"intent_secret": payment.payment_intent_secret})


class WebhookView(ViewSet):
    permission_classes = [AllowAny]

    @csrf_exempt
    @action(methods=["POST"], detail=False, url_name="stripe", url_path="stripe",
            permission_classes=[AllowAny])
    def stripe_webhook(self, request):
        event = None
        payload = request.body
        data = request.data
        sig_header = request.headers['STRIPE_SIGNATURE']

        client = StripeClient()
        status = client.webhook(data, payload, sig_header)
        return Response({"success": status}, status=200)


class XeroView(ViewSet):
    permission_classes = [AllowAny]
    client = XeroClient

    @action(methods=["GET"], detail=False, url_name="disconnect", url_path="disconnect",
            permission_classes=[IsAuthenticated])
    def disconnect(self, request):
        xero = Xero.objects.first()
        if not xero:
            return Response({"message": "already disconnected"})
        self.client(xero.access_token).disconnect_xero(xero.access_token)
        return Response({"message": "Disconnected"})

    @action(methods=["GET"], detail=False, url_name="invoices", url_path="invoices",
            permission_classes=[IsAuthenticated])
    def invoices(self, request):
        xero = Xero.objects.first()
        if not xero:
            return Response({"message": "Connect Xero from crm"})
        return Response({"data": self.client(xero.access_token).get_invoices(xero.tenant_id)})

    @action(methods=["GET"], detail=False, url_name="connections", url_path="connections",
            permission_classes=[IsAuthenticated])
    def connections(self, request):
        xero = Xero.objects.first()
        if not xero:
            return Response({"message": "Connect Xero from crm"})
        return Response({"data": self.client(xero.access_token).get_connections()})

    @action(methods=["GET"], detail=False, url_name="callback", url_path="callback",
            permission_classes=[AllowAny])
    def callback(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code:
            return redirect("login")
        user = Xero.objects.all().first()
        if not user:
            return redirect("login")
        client = self.client()
        state_token = client.decrypt_token(state)
        token_user = Token.objects.filter(key=state_token).first()
        if not code or not token_user:
            return redirect("login")
        tokens = client.get_user_tokens(code)
        login(request, token_user.user)
        if tokens:
            xero = Xero.objects.first()
            xero.refresh_token = tokens.get("refresh_token", xero.refresh_token)
            xero.access_token = tokens.get("access_token", xero.access_token)
            xero.expire_token = timezone.now() + timedelta(seconds=tokens.get("expires_in", 1800))
            xero.save()

        return redirect("xero")

    @action(methods=["GET"], detail=False, url_name="login", url_path="login",
            permission_classes=[IsAdminUser])
    def xero_login(self, request):
        client = self.client()
        state = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
        url = client.get_login_url(state)
        Xero.objects.get_or_create(admin_user=request.user)
        return Response({"url": url})


class GmailLogin(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        api = GoogleAPI()
        return Response({"gmail_login_uri": api.get_login_url(request.user)})

    @action(methods=['GET'], detail=False, url_path="callback", url_name="callback", permission_classes=[AllowAny])
    def callback(self, request, *args, **kwargs):
        auth_code = request.GET.get('code')
        state = request.GET.get('state')
        if not auth_code or not state:
            return redirect(settings.FRONTEND_CRM_URL)
        api = GoogleAPI()
        token = api.decrypt_token(state)
        user_token = Token.objects.filter(key=token).first()
        if not user_token:
            return redirect(settings.FRONTEND_CRM_URL)
        user = user_token.user
        login(request, user)
        tokens = api.get_token_from_code(auth_code)
        if tokens and not tokens.get("error"):
            gmail, _ = GoogleAuth.objects.get_or_create(user=user)
            gmail.expire_token = datetime.now() + timedelta(seconds=tokens['expires_in'])
            gmail.access_token = tokens.get('access_token', "")
            gmail.refresh_token = tokens.get('refresh_token', "")
            gmail.save()
            user_info = api.get_user_info(gmail.access_token)
            if user_info:
                if user_info.get("email"):
                    gmail.email = user_info.get("email", user.email)
                gmail.name = user_info.get("name", user.full_name)
            else:
                gmail.name = user_info.get("name", user.full_name)
                gmail.email = user_info.get("email", user.email)
            gmail.save()
            response = redirect(settings.FRONTEND_CRM_URL)
        else:
            response = redirect(settings.FRONTEND_CRM_URL)
        return response
