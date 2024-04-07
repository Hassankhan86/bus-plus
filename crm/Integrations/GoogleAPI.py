import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.signing import TimestampSigner
from django.core.signing import BadSignature
from googleapiclient.discovery import build
from oauth2client import client
import iso8601
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.authtoken.models import Token
from urllib.parse import quote, urlencode
from datetime import datetime, timedelta
from crm.models import GoogleAuth
from dateutil.parser import parse
from django.utils import timezone


class GoogleAPI():
    def __init__(self):
        self.client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.authority = settings.GOOGLE_AUTHORITY
        self.scope_auth_uri = settings.GOOGLE_SCOPES_AUTH_URI
        self.scopes = settings.GOOGLE_SCOPES
        self.user_info_uri = settings.GOOGLE_USER_INFO_URI
        self.token_obtain_uri = settings.GOOGLE_ACCESS_TOKEN_OBTAIN_URL
        self.secure_key = settings.SECRET_KEY

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

    def is_valid_gmail_token(self, token: GoogleAuth):
        try:
            if not token:
                return None
            if token and token.expire_token.replace(tzinfo=None) > datetime.now() and token.access_token:
                return token.access_token

            if token and token.expire_token.replace(tzinfo=None) < datetime.now() and not token.refresh_token:
                return None
            if token and (
                    token.expire_token.replace(
                        tzinfo=None) < datetime.now() or not token.access_token) and token.refresh_token:
                return self.refresh_access_token(gmail=token)
        except:
            pass
        return None

    def schedule_gmail_event(self, gmail: GoogleAuth, event):
        access_token = self.is_valid_gmail_token(gmail)
        if access_token:
            try:
                credentials = client.AccessTokenCredentials(access_token, 'USER_AGENT')
                service = build('calendar', 'v3', credentials=credentials)

                event = service.events().insert(calendarId="primary", body=event,
                                                conferenceDataVersion=1,
                                                sendUpdates='all').execute()
                return event
            except Exception as e:
                return False
        return False

    def get_token_from_code(self, auth_code):
        data = {
            'code': auth_code,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        r = requests.post(self.token_obtain_uri, data=data)
        try:
            return r.json()
        except:
            return {}

    def get_user_info(self, token):
        response = requests.get(
            self.user_info_uri,
            params={'access_token': token}
        )
        try:
            return response.json()
        except Exception as ex:
            return {}

    def get_login_url(self, user):
        user_token, _ = Token.objects.get_or_create(user=user)
        state = self.encrypt_token(user_token)
        params = {'client_id': self.client_id,
                  'redirect_uri': self.redirect_uri,
                  'response_type': 'code',
                  'scope': f' '.join(
                      f"{self.scope_auth_uri if '.' in i or 'calendar' in i else ''}{i}" for i in self.scopes),
                  'prompt': 'select_account',
                  'access_type': 'offline',
                  "state": state
                  }
        authorize_url = f"{self.authority}?{urlencode(params)}"
        return authorize_url

    def refresh_access_token(self, gmail: GoogleAuth):
        if not gmail.refresh_token:
            return False
        data = {
            'refresh_token': gmail.refresh_token,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'refresh_token'
        }
        r = requests.post(self.token_obtain_uri, data=data)
        try:
            tokens = r.json()
            gmail.expiresOn = datetime.now() + timedelta(seconds=tokens['expires_in'])
            gmail.oauth_token = tokens.get('access_token', "")
            gmail.refresh_token = tokens.get('refresh_token', gmail.refresh_token)
            gmail.save()
            return gmail.access_token
        except:
            return {}

    def format_gmail_calendar_events(sefl, events):
        gmail_events = []
        for event in events.get("items",[]):
            try:
                start = iso8601.parse_date(event['start'].get('dateTime', event['end'].get('date', )))
                end = iso8601.parse_date(event['end'].get('dateTime', event['end'].get('date', )))
                new_event = {
                    'start': start.astimezone(timezone.get_current_timezone()).isoformat(),
                    'startStr': str(start.astimezone(timezone.get_current_timezone()).isoformat()),
                    'endStr': str(end.astimezone(timezone.get_current_timezone()).isoformat()),
                    'end': end.astimezone(timezone.get_current_timezone()).isoformat(),
                    'time_zone': event['start'].get('timeZone'),
                    'description': event.get('description'),
                    'status': event.get('status'),
                    "extendedProps":{
                        'meetingLink': event.get('hangoutLink'),
                    },

                    'title': event.get('summary'),
                    'display': 'auto'
                }
                gmail_events.append(new_event)
            except Exception as ex:
                print(ex)

        return gmail_events

    def get_gmail_events(self, google: GoogleAuth, start_date=None, end_date=None):
        access_token = self.is_valid_gmail_token(google)
        if access_token:
            try:
                credentials = client.AccessTokenCredentials(access_token, 'USER_AGENT')
                service = build('calendar', 'v3', credentials=credentials)
                if start_date:
                    s_d = parse(str(start_date)) - relativedelta(days=1)
                    start_date = s_d.astimezone(timezone.get_current_timezone()).isoformat()
                if end_date:
                    e_d = parse(str(end_date)) + relativedelta(days=1)
                    end_date = e_d.astimezone(timezone.get_current_timezone()).isoformat()
                google_calendar_events = service.events().list(
                    calendarId="primary", timeMin=start_date, timeMax=end_date,
                    showDeleted=False, singleEvents=True,
                    maxResults=1000).execute()
                return self.format_gmail_calendar_events(google_calendar_events)
            except Exception as e:
                return []
        return []
