import json
from datetime import timedelta

from django.conf import settings
import requests
import base64
import urllib.parse

from django.core.signing import TimestampSigner, BadSignature
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


class XeroClient:
    def __init__(self, access_token=""):
        self.client = settings.XERO_CLIENT
        self.secret = settings.XERO_SECRET
        self.redirect_uri = settings.XERO_REDIRECT_URI
        self.login_url = "https://login.xero.com/identity/connect/authorize?"
        self.scope = urllib.parse.quote('openid offline_access accounting.transactions profile email accounting.contacts accounting.settings ')
        self.exchange_url = 'https://identity.xero.com/connect/token'
        self.token_url = 'https://identity.xero.com/connect/token'
        credentials = "{0}:{1}".format(self.client, self.secret)
        self.basic_token = base64.urlsafe_b64encode(credentials.encode()).decode()
        self.access_token = access_token
        self.api = "https://api.xero.com/"
        self.secure_key = "buses_plus_zohaib@gmail.com"

    def get_login_url(self, state=""):
        return f"""{self.login_url}response_type=code&client_id={self.client}&redirect_uri={self.redirect_uri}&scope={self.scope}&state={state}"""

    def encrypt_token(self, key):
        signer = TimestampSigner(self.secure_key)
        signed_value = signer.sign(key)
        encoded_value = urlsafe_base64_encode(force_bytes(signed_value))
        return encoded_value

    def decrypt_token(self, encrypted_value):
        try:
            signed_value = urlsafe_base64_decode(encrypted_value)
            signer = TimestampSigner(self.secure_key)
            value = signer.unsign(force_str(signed_value))
            return value
        except (ValueError, TypeError, BadSignature):
            return None

    def get_user_tokens(self, code):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "Authorization": f"Basic {self.basic_token}"
        }
        response = requests.post(self.exchange_url, headers=headers, data=data)
        print(response.json())
        if response.status_code == 200:
            return response.json()
        return {}

    def get_refresh_token(self, ref_token):
        from booking.models import Xero
        xero = Xero.objects.filter(refresh_token=ref_token).first()
        if not xero:
            return {}
        response = requests.post(self.token_url,
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded',
                                     "Authorization": f"Basic {self.basic_token}"
                                 },
                                 data={
                                     'grant_type': 'refresh_token',
                                     'refresh_token': ref_token
                                 })
        if response.status_code == 200:
            token = response.json()
            xero.refresh_token = token.get("refresh_token", xero.refresh_token)
            xero.access_token = token.get("access_token", xero.access_token)
            xero.expire_token = timezone.now() + timedelta(seconds=token.get("expires_in", 1800))
            xero.save()
            return token
        return {}

    def disconnect_xero(self, token):
        url = "https://identity.xero.com/connect/revocation"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "Authorization": f"Basic {self.basic_token}"
        }
        data = {
            'token': token
        }
        res = requests.post(url, headers=headers, data=data)
        print(res.json())
        return {}

    def is_valid_token(self, access_token):
        from booking.models import Xero
        xero = Xero.objects.filter(access_token=access_token).first()
        if not xero or not xero.is_valid_token():
            return False
        return xero.access_token

    def get(self, endpoint,extra_header ={}, params={}):
        access_token = self.is_valid_token(self.access_token)
        if not access_token:
            return {"message": "Not able to fetch data due to exited of invalid tokens"}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept":"application/json",
            "Content-Type":"application/json",
            **extra_header
        }
        res = requests.get(f"{self.api}{endpoint}", headers=headers, params=params)
        return res.json()

    def post(self, endpoint,extra_header ={}, params=None, data=None):
        access_token = self.is_valid_token(self.access_token)
        if not access_token:
            return {"message": "Not able to fetch data due to exited of invalid tokens"}
        headers = {
            "Accept":"application/json",
            "Content-Type":"application/json",
            "Authorization": f"Bearer {self.access_token}",
            **extra_header
        }
        res = requests.post(f"{self.api}{endpoint}", headers=headers, params=params, json=data)
        return res.json()

    def get_invoices(self, tenant_id):
        return self.get("api.xro/2.0/Invoices",extra_header={"xero-tenant-id":tenant_id})

    def create_invoice(self, tenant_id,data):
        return self.post("api.xro/2.0/Invoices", extra_header={"xero-tenant-id": tenant_id},data=data)

    def make_payment(self, tenant_id, data):
        return self.post("api.xro/2.0/Payments", extra_header={"xero-tenant-id": tenant_id},data=data)

    def get_accounts(self, tenant_id):
        return self.get("api.xro/2.0/Accounts", extra_header={"xero-tenant-id": tenant_id})

    def get_connections(self):
        return self.get("connections")
