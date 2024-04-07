# signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from booking.models import Order, User, ContactUs
from booking.tasks import cancel_unpaid_reservations, contactus_email
from django.utils import timezone
from datetime import timedelta
from booking.CONSTANT import *


# method for updating
@receiver(post_save, sender=Order, dispatch_uid="schedule_order")
def schedule_order(sender, instance, created, **kwargs):
    if created and instance == ORDER_STATUS[0][0]:
        deadline = timezone.now() + timedelta(minutes=settings.BOOKING_PAYMENT_DEADLINE_MINUTES) + timedelta(
            days=settings.BOOKING_PAYMENT_DEADLINE_DAYS) + timedelta(hours=settings.BOOKING_PAYMENT_DEADLINE_HOURS)
        cancel_unpaid_reservations.apply_async(args=[instance.id], eta=deadline)
    print(instance)


@receiver(post_save, sender=ContactUs)
def send_contact_us_email(sender, instance, created, **kwargs):
    if created:
        subject = 'New Contact Form Submission'
        message = f'A new contact form submission from {instance.name}:\n\n{instance.message} \n\n {instance.email}'
        contactus_email.delay(subject, message)
