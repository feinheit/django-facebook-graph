from django.contrib import admin
from django.conf import settings

from models import User, Photo, Page, Event, Request, TestUser


class AdminBase(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.get_from_facebook(save=True, request=request)
    
    def profile_link(self, obj):
        if obj.facebook_link:
            return '<a href="%s" target="_blank"><img src="%s/picture?type=small" /></a>' % (obj.facebook_link, obj.graph_url)
        else:
            return '<img src="http://graph.facebook.com/%s/picture" />' % (obj.id)
    profile_link.allow_tags = True

class UserAdmin(AdminBase):
    list_display = ('id', 'profile_link', 'access_token', 'user', '_name', 'created', 'updated',)
    readonly_fields = ('friends', '_name', '_first_name', '_last_name', '_link', '_birthday', '_email', '_location', '_gender', '_graph')
    search_fields = ('id', '_name')
    
admin.site.register(User, UserAdmin)

if settings.DEBUG:
    admin.site.register(TestUser, UserAdmin)
    

class PhotoAdmin(AdminBase):
    list_display = ('_id', '_name', 'like_count', '_from_id')
    readonly_fields = ('fb_id', '_name', '_likes', '_graph', '_from_id', '_like_count')
admin.site.register(Photo, PhotoAdmin)


class PageAdmin(AdminBase):
    list_display = ('id', 'profile_link', 'slug', '_name', '_picture', '_likes')
    readonly_fields = ('_name', '_picture', '_likes', '_graph', '_link')
admin.site.register(Page, PageAdmin)

"""
class ApplicationAdmin(AdminBase):
    list_display = ('id', 'profile_link', 'slug', '_name', '_picture', '_likes','api_key', 'secret')
    readonly_fields = ('_name', '_picture', '_likes', '_graph', '_link')
admin.site.register(Application, ApplicationAdmin)
"""

class EventAdmin(AdminBase):
    list_display = ('id', 'profile_link', '_owner', '_name', '_description', '_start_time', '_end_time', '_location', '_venue', '_privacy')
    readonly_fields = ('_graph', '_owner', '_name', '_description', '_start_time', '_end_time', '_location', '_venue', '_privacy', '_updated_time')
    list_display_links = ('id',)
admin.site.register(Event, EventAdmin)


class RequestAdmin(AdminBase):
    list_display = ('id', '_application', '_to', '_from', '_data', '_message', '_created_time')
    readonly_fields = ('_graph', '_application', '_to', '_from', '_data', '_message', '_created_time')
admin.site.register(Request, RequestAdmin)