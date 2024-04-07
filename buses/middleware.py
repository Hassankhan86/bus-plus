# maintenance_middleware.py
import logging

from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.urls import reverse
from django.shortcuts import redirect, render
from django.conf import settings
import time
from django.core.cache import cache

from django.http import HttpResponse
from django.contrib import messages

from booking.tasks import contactus_email
from booking.utils import send_email

class CSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request method is not safe (e.g., POST, PUT, DELETE)
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            if not self._is_valid_csrf(request):

                messages.error(request, "Session timeout please try again.")
                return redirect(request.get_full_path())

        response = self.get_response(request)
        return response

    def _is_valid_csrf(self, request):

        csrf_token = request.META.get("HTTP_X_CSRFTOKEN", "")
        csrf_token_cookie = request.COOKIES.get("csrftoken", "")
        return csrf_token == csrf_token_cookie


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            return HttpResponseServerError("Server is under maintenance. Please try again later.")

        response = self.get_response(request)
        return response


class AuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(reverse('admin:index')) or request.path.startswith('/crm/'):
            if not request.user.is_authenticated:
                login_url = '/login/'
                current_url = request.get_full_path()
                redirect_url = f"{login_url}?next={current_url}"
                return redirect(redirect_url)
            elif not (request.user.is_staff or request.user.is_superuser):
                return redirect('/')
        response = self.get_response(request)
        return response

