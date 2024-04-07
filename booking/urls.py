

from django.urls import path,include
from django.contrib.auth import views as auth_views
from . import views
from booking.views import *
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path("api/", include("booking.api.urls")),
    path("", IndexPageView.as_view(),name="index"),

    path("booking", Booking.as_view(),name="booking"),
    path("booking/edit/<str:pk>/", login_required(EditBookingView.as_view()),name="booking-edit"),
    path("my-order", login_required(MyOrderPageView.as_view()),name="my-order"),
    path("booking/get_more_buses", get_more_buses,name="get_more_buses"),
    path("checkout/<str:pk>/", CheckoutView.as_view(), name="checkout"),
    path("payment/<str:pk>/", PaymentView.as_view(), name="payment"),
    path("payment-cash", login_required(PaymentCashView.as_view()), name="payment-cash"),
    path("confirm-booking/<str:pk>/", ConfirmBooking.as_view(),name="confirm-booking"),

    path('about/', AboutUsPageView.as_view(), name='about'),
    path('baggage/', BaggagePageView.as_view(), name='baggage'),
    path('trip-reservation/', TripReservationPageView.as_view(), name='trip-reservation'),
    path('contact/', ContactPageView.as_view(), name='contact'),
    path('page-404/', ErrorPageView.as_view(), name='page-404'),
    path('blog-single/', BlogSinglePageView.as_view(), name='blog-single'),
    path('blog-sidebar/', BlogSidebarPageView.as_view(), name='blog-sidebar'),
    path('faqs/', FaqPageView.as_view(), name='faq'),
    path('bus-fleet/', BusFleetPageView.as_view(), name='bus-fleet'),
    path('on-board-entertainment/',OnBoardEntertainmentPageView.as_view(), name='on-board-entertainment'),
    path('bus-features/', BusFeaturesPageView.as_view(), name='bus-features'),
    path('payment-complete/', PaymentCompletePageView.as_view(), name='payment-complete'),
    path('payment-received/<str:pk>/', PaymentReceivedPageView.as_view(), name='payment-received'),
    path('my-order/<str:pk>/', login_required(PaymentReceivedPageView.as_view()), name='my-order-id'),
    path('initiate-refund', login_required(RefundOrder.as_view()), name='initiate-refund'),
    path('route-map/', RouteMapPageView.as_view(), name='route-map'),
    path('customer-with-disabilities/', CustomerWithDisabilitiesPageView.as_view(), name='customer-with-disabilities'),
    path('payment-and-ticket/', PaymentAndTicketsPageView.as_view(), name='payment-and-ticket'),
    path('manage-my-booking/', ManageMyBookingPageView.as_view(), name='manage-my-booking'),




    path('login/', LoginView.as_view(), name='login'),
    path('send-email/', SendEmailView.as_view(),name='send-email'),

    path('signup/', SignupView.as_view(), name='signup'),
    path('logout', login_required(Logout.as_view()), name='logout'),
    path('password-reset-done/', PasswordResetDonePageView.as_view(), name='password-reset-done'),
    path('password-reset-confirm/', PasswordResetConfirmPageView.as_view(), name='password-reset-confirm'),
    path('password-reset-complete/', PasswordResetCompletePageView.as_view(), name='password-reset-complete'),







    path('schedule-meeting', ScheduleMeeting.as_view(), name='meet'),
]
