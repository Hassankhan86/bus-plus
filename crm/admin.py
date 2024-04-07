from django.contrib import admin
from crm.models import *


# Register your models here.
class GoogleAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'name', 'is_valid_token']
    readonly_fields = ['user', 'refresh_token', 'name', 'access_token', 'expire_token', 'email']


admin.site.register(GoogleAuth, GoogleAdmin)
