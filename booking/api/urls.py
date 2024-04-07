from django.urls import path, include
from booking.api.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("stripe", StripView, basename="stripe")
router.register("webhook", WebhookView, basename="stripe")
router.register("xero", XeroView, basename="xero")
router.register("google/login", GmailLogin, basename="google")


urlpatterns = [
    path("", include(router.urls)),
    path("get-cities", CitiesView.as_view(), name="get_cities"),
    path("add-trip", TripeCreateView.as_view(), name="add-trip"),
    path("add-stops", StopsListView.as_view(), name="add-stops"),
    path("check-coupon", CheckCouponView.as_view(), name="check-coupon"),
    path("get_insurances/<str:pk>/", InsurancesView.as_view(), name="get_insurances"),

]
