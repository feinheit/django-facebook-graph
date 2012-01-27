from django.contrib import admin

from facebook.modules.base import AdminBase

from .models import Event


class EventAdmin(AdminBase):
    list_display = ('id', 'profile_link', '_owner', '_name', '_description', '_start_time', '_end_time', '_location', '_venue', '_privacy')
    readonly_fields = ('_graph', '_owner', '_name', '_description', '_start_time', '_end_time', '_location', '_venue', '_privacy', '_updated_time')
    list_display_links = ('id',)

admin.site.register(Event, EventAdmin)