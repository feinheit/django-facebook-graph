from django.contrib import admin
from django.conf import settings

from models import User, Photo, Page, Event, Request, TestUser, Post
from utils import get_graph


class AdminBase(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        graph = get_graph(request, force_refresh=True, prefer_cookie=True)
        obj.get_from_facebook(save=True, graph=graph)
    
    def profile_link(self, obj):
        if obj.facebook_link:
            return '<a href="%s" target="_blank"><img src="%s/picture?type=square" /></a>' % (obj.facebook_link, obj.graph_url)
        else:
            return '<img src="http://graph.facebook.com/%s/picture" />' % (obj.id)
    profile_link.allow_tags = True
    
    def change_view(self, request, object_id, extra_context=None):
        fb_context = {
            'facebook_apps': settings.FACEBOOK_APPS.keys(),
            'graph' : get_graph(request, force_refresh=True, prefer_cookie=True)
        }
        return super(AdminBase, self).change_view(request, object_id,
            extra_context=fb_context)

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
    list_display = ('id', '_application_id', '_to', '_from', '_data', '_message', '_created_time')
    readonly_fields = ('_graph', '_application_id', '_to', '_from', '_data', '_message', '_created_time')
admin.site.register(Request, RequestAdmin)

class PostAdmin(AdminBase):
    def picture_link(self, obj):
            return '<img src="%s" />' % (obj._picture)
    picture_link.allow_tags = True
    picture_link.short_description = u'picture'
    
    def icon_link(self, obj):
            return '<img src="%s" alt="%s" width="16" height="16"/>' % (obj._icon, obj._type)
    icon_link.allow_tags = True
    icon_link.short_description = u'icon'
    
    list_display = ('icon_link', 'id', '_message', '_type', 'picture_link')
    list_display_links = ('id',)
    readonly_fields = ('_graph', '_application', '_to', '_from', '_message', '_picture',
                       '_properties', '_actions', '_privacy', '_likes', '_comments', '_targeting')
    date_hierarchy = '_updated_time'
    list_filter = ('_type',)
    
    
admin.site.register(Post, PostAdmin)
    
