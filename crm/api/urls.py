from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


urlpatterns = [
    path("", include(router.urls)),
    path('get_chart_data/', earnings_chart, name='get_chart_data'),
    path('bus-image/delete/<str:pk>/', delete_bus_image, name='delete_bus_image'),
    path('refund-request', refund_request_view, name='refund-request'),
    path('save-trip-details', save_featured_trip_details, name='save-trip-details'),
    path('events', get_calendar_events, name='google-events'),

]
