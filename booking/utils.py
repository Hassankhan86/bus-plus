from django.conf import settings
from django.core.mail import send_mail as send_emails
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from datetime import datetime, timedelta
from django.core.mail import EmailMessage

def convert_to_timedelta(time_str):
    parts = time_str.split()
    hours = int(parts[0])
    minutes = int(parts[2])
    return timedelta(hours=hours, minutes=minutes)


# Convert timedelta to formatted time string like "36 h 35 m"
def convert_to_time_string(time_delta):
    hours = time_delta.days * 24 + time_delta.seconds // 3600
    minutes = (time_delta.seconds % 3600) // 60
    return f"{hours} h {minutes} m"


def round_time(time):
    minutes = time.minute
    if minutes < 30:
        time = time.replace(minute=30)
    elif minutes < 60 and minutes > 30:
        time = time.replace(minute=0)
    else:
        time = (time + timedelta(hours=1)).replace(minute=0)
    return time


def add_stop_time_in_route(pickup_time_str, date_str, stop_time=0, estimated_time_mins=0):
    pickup_time = datetime.strptime(pickup_time_str, "%I%M%p").time()

    # Parse the date string
    return_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()

    # Combine the date and time into a single datetime object
    return_datetime = datetime.combine(return_date, pickup_time)
    return_datetime += timedelta(minutes=stop_time)
    return_datetime += timedelta(minutes=convert_time_to_minutes(estimated_time_mins))
    remaining_minutes = 30 - (return_datetime.minute % 30) if return_datetime.minute < 30 else 60 - (
                return_datetime.minute % 60)
    return_datetime += timedelta(minutes=remaining_minutes)
    return_datetime_str = return_datetime.strftime("%I%M%p")
    pick_date = return_datetime.date()
    return pick_date, return_datetime_str


def send_email(subject, message, recipient_list,html_message=""):
    email = EmailMessage(
        'Order Confirmation Email',
        html_message,
        settings.EMAIL_HOST_USER,
        recipient_list)
    email.fail_silently = False
    email.content_subtype = "html"
    try:
        email.send()
    except Exception as ex:
        print(ex)
    # send_emails(subject, message if not html_message else html_message, email_from, recipient_list, fail_silently=False)


def add_form_errors_messages(form, request):
    if form.errors:
        messages.add_message(request, messages.ERROR, _("Please correct the following errors:"))
        for field_errors in form.errors:
            messages.add_message(request, messages.ERROR,
                                 f"{field_errors.replace('_', ' ')}: {form.errors[field_errors][0]}")


def convert_time_to_minutes(time_str):
    time_str = time_str.strip().lower()
    hours = 0
    minutes = 0

    if 'h' in time_str:
        hours_str, minutes_str = time_str.split('h')
        hours = int(hours_str.strip())
        if 'm' in minutes_str:
            minutes = int(minutes_str.split('m')[0].strip())
    elif 'm' in time_str:
        minutes = int(time_str.split('m')[0].strip())

    total_minutes = hours * 60 + minutes
    return total_minutes


def parse_str_date_time(str_date, str_time, extra_time=0):
    pickup_time = datetime.strptime(str_time, "%I%M%p").time()
    return_date = datetime.strptime(str(str_date), "%Y-%m-%d").date()
    return_datetime = datetime.combine(return_date, pickup_time)
    return_datetime += timedelta(minutes=extra_time)
    return return_datetime


def parse_return_time_and_date(pickup_time_str, date_str, estimated_time_mins):
    # Parse the pickup time string
    pickup_time = datetime.strptime(pickup_time_str, "%I%M%p").time()

    # Parse the date string
    return_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()

    # Combine the date and time into a single datetime object
    return_datetime = datetime.combine(return_date, pickup_time)
    return_datetime += timedelta(minutes=convert_time_to_minutes(estimated_time_mins))
    return_datetime_str = return_datetime.strftime("%I%M%p")

    return return_datetime_str


def serializer_errors_list(serializer):
    errors_list = []
    for field, errors in serializer.errors.items():
        for error in errors:
            errors_list.append(f"{f'{field}:' if field != 'non_field_errors' else ''}{error}")
    return errors_list


def is_valid_self_drive_schedule(datetime_obj):
    schedule = settings.SELF_DRIVE_SCHEDULE
    day = datetime_obj.strftime('%A')
    current_time = datetime_obj.time()

    if day in schedule:
        start_time_str, end_time_str = schedule[day]

        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()

        if start_time <= current_time <= end_time:
            return True, ""
        return False, f"Self-drive pickup is available on {day} from {start_time_str} to {end_time_str}."

    return False, "Self-drive pickup is not available on this day."
