from django.contrib.auth.models import User
from django.db import models

class FacebookUser(models.Model):
    profile_url = models.URLField(verify_exists=False)
    access_token = models.CharField(max_length=250, blank=True)
    user = models.OneToOneField(User)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)