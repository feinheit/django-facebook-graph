from django.conf import settings
from django.contrib import admin

from facebook.modules.base import AdminBase

from .models import User

class UserAdmin(AdminBase):
    list_display = ('id', 'profile_link', 'access_token', 'user', '_name', 'created', 'updated',)
    readonly_fields = ('friends', '_name', '_first_name', '_last_name', '_link', '_birthday', '_email', '_location', '_gender', '_graph')
    search_fields = ('id', '_name')

if not hasattr(settings, 'FACEBOOK_ADMIN'):
    admin.site.register(User, UserAdmin)
