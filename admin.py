from django.contrib import admin

from models import FacebookUser

class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'access_token', 'user', '_name', 'created', 'updated', '_link')
    readonly_fields = ('_name', '_first_name', '_last_name', '_link', '_birthday', '_email', '_location', '_gender', '_graph')
admin.site.register(FacebookUser, FacebookUserAdmin)