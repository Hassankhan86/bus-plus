from django.urls import path,include
from crm.views import *

urlpatterns = [
    path("api/", include("crm.api.urls")),
    path("", dashboard, name="dashboard"),
    # Buses
    path('buses/<int:bus_id>/delete/', delete_bus, name='delete_bus'),
    path("buses/",  BusesListView.as_view(), name="buses-list"),
    path("add-buses/",  BusesAddView.as_view(), name="add-buses"),
    path('buses/<str:bus_id>/', BusManageView.as_view(), name='manage-bus'),

    # Faqs
    path('faqs/<str:faq_id>/', FaqManageView.as_view(), name='manage-faq'),
    path("add-faq/", FaqAddView.as_view(), name="add-faq"),
    path("add-faq-category/", FaqCategoryAddView.as_view(), name="add-faq-category"),
    path("faqs/", FaqsListView.as_view(), name="faq-list"),
    path('faqs/<int:faq_id>/delete/', delete_faq, name='delete_faq'),

    # Users
    path("users/", UserListView.as_view(), name="users"),
    path("add-user/", add_user, name="add-user"),

    # Orders
    path("orders/", OrderListView.as_view(), name="orders"),
    path("orders/<str:pk>/", OrderDetailedVIew.as_view(), name="orders_view"),
    # coupon

    path("add-coupon/", CouponAddView.as_view(), name="add-coupon"),
    path("coupons/<str:coupon_id>/", CouponManageView.as_view(), name='manage-coupon'),
    path("coupons/", CouponListView.as_view(), name="coupon-list"),
    path('coupons/<int:pk>/delete/', delete_coupon, name='delete_coupon'),
    
    
    # Trips
    path("trips/", TripListView.as_view(), name="trip-list"),
    path("featuredTrips/", FeaturedTripListView.as_view(), name="featured-trip"),
    path("featured-trip-create/", FeaturedTripCreateView.as_view(), name="featured-trip-create"),
    path("featuredTrips/<str:trip_id>/", FeaturedTripManageView.as_view(), name='manage-featured-trip'),
    # Payments
    path("payments/", PaymentListView.as_view(), name="payments"), 
    path("order-payments", UpdateOrderCashPayment.as_view(), name="cash-payments"),
    path("order-reject<str:pk>/", MarkRejected.as_view(), name="order-reject"),
    path("order-complete<str:pk>/", MarkCompleted.as_view(), name="order-complete"),


    # Payments
    path("refunds/", RefundListView.as_view(), name="refunds"),
    path("refunds-requests/", RefundRequestView.as_view(), name="refunds-requests"),

    # Cities
    path("add-city/", CityAddView.as_view(), name="add-city"),
    path("cities/", CityListView.as_view(), name="city-list"),
    path('cities/<str:city_id>/', CityManageView.as_view(), name='manage-city'),
    path('cities/<int:pk>/delete/', delete_city, name='delete_city'),


    # Stops Charges

    path('stopCharges/', StopChargesListView.as_view(), name="stop-charges-list"),
    path('add-stop-charges/', StopChargesAddView.as_view(), name="add-stop-charges"),
    path('stopCharges/<str:stop_id>/', StopChargesManageView.as_view(), name='manage-stop-charges'),
    path('stopCharges/<int:pk>/delete/', delete_stop_charges, name='delete-stop-charges'),

    # License
    path('licenses/', LicenseListView.as_view(), name="license-list"),
    path('add-license/', LicenseAddView.as_view(), name="add-license"),
    path('licenses/<str:license_id>/', LicenseManageView.as_view(), name='manage-license'),
    path('licenses/<int:pk>/delete/', delete_license, name='delete_license'),

    # Insurance
    path('insurances/', InsuranceListView.as_view(), name="insurance-list"),
    path('add-insurance/', InsuranceAddView.as_view(), name="add-insurance"),
    path('insurance/<str:insurance_id>/', InsuranceManageView.as_view(), name='manage-insurance'),
    path('insurances/<int:pk>/delete/', delete_insurance, name='delete_insurance'),

    # Trip Category
    path('tripCategories/', TripCategoryListView.as_view(), name="trip-category-list"),
    path('add-trip-category/', TripCategoryAddView.as_view(), name="add-trip-category"),
    path('tripCategories/<str:trip_category_id>/', TripCategoryManageView.as_view(), name='manage-trip-category'),
    path('tripCategories/<int:pk>/delete/', delete_trip_category, name='delete_trip_category'),
    # Xero
    path('xero', XeroView.as_view(), name='xero'),
    path('crm-xero-login', XeroViewLogin.as_view(), name='crm-xero-login'),
    path('crm-xero-logout', XeroViewLogout.as_view(), name='crm-xero-logout'),


    path('google', GoogleCalendarView.as_view(), name='crm-google'),
    path('crm-google-login', GoogleViewLogin.as_view(), name='crm-google-login'),
    path('crm-google-logout', GoogleViewLogout.as_view(), name='crm-google-logout'),


]
