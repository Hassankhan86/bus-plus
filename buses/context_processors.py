# context_processors.py
from django.middleware.csrf import get_token
from django.conf import settings
from booking.CONSTANT import ORDER_STATUS
from booking.models import Order



def crm_data(request):
    devloped_by = settings.DEVELOPEDBY
    self_drive_address = settings.SELF_DRIVE_PICKUP_ADDRESS
    IS_BUSES_SHOW_TO_USER = settings.IS_BUSES_SHOW_TO_USER
    orders = Order.objects.filter(order_status=ORDER_STATUS[2][0])[:10]
    return {'notify_orders': orders,"devloped_by":devloped_by, "IS_BUSES_SHOW_TO_USER": IS_BUSES_SHOW_TO_USER,"self_drive_address":self_drive_address}
