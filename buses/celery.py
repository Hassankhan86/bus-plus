# settings.py

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import  settings
# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buses.settings')

app = Celery('buses', broker='redis://127.0.0.1:6379')

# Celery configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'complete_order_statues': {
        'task': 'booking.tasks.update_completed_orders',
        'schedule': crontab(minute="*/1"),
    },
}
app.conf.timezone = settings.TIME_ZONE