from django.contrib import admin

from models import FacebookUser

class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile_url', 'user')
admin.site.register(FacebookUser, FacebookUserAdmin)