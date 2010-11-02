from django.contrib.auth.models import User
from django.db import models

class FacebookUser(models.Model):
    profile_url = models.URLField(verify_exists=False)
    access_token = models.CharField(max_length=250, blank=True)
    user = models.OneToOneField(User, blank=True, null=True)
    
    """ Cached Facebook Graph fields """
    _first_name = models.CharField(max_length=50, blank=True, null=True)
    _last_name = models.CharField(max_length=50, blank=True, null=True)
    _name = models.CharField(max_length=100, blank=True, null=True)
    _link = models.URLField(verify_exists=False, blank=True, null=True)
    _birthday = models.DateField(blank=True, null=True)
    _email = models.EmailField(blank=True, null=True)
    _location = models.CharField(max_length=70, blank=True, null=True)
    _gender = models.CharField(max_lenght=10, blank=True, null=True)
    _locale = models.CharField(max_length=6, blank=True, null=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    