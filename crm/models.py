from django.db import models

# Create your models here.

from booking.models import User
from django.utils import timezone


class GoogleAuth(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=60,null=True,blank=True)
    email = models.EmailField(max_length=60,null=True,blank=True)
    access_token = models.TextField(null=True,blank=True)
    refresh_token = models.TextField(null=True,blank=True)
    expire_token = models.DateTimeField(null=True,blank=True)

    def is_valid_token(self):
        from crm.Integrations.GoogleAPI import GoogleAPI

        if not self.expire_token is not None and self.expire_token > timezone.now():
            return True
        elif self.refresh_token:
            client = GoogleAPI()
            res = client.refresh_access_token(self)
            return True if res else False
        else:
            return False
