from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from facebook.graph import get_graph
from modules.profile.application.admin import ScoreAdmin
from modules.profile.user.admin import UserAdmin
from modules.connections.post.admin import PostAdmin
from modules.base import AdminBase

from all.models import *


class PhotoAdmin(AdminBase):
    list_display = ('_id', '_name', 'like_count', '_from_id')
    readonly_fields = ('fb_id', '_name', '_likes', '_graph', '_from_id', '_like_count')


class EventAdmin(AdminBase):
    list_display = ('id', 'profile_link', '_owner', '_name', '_description', '_start_time', '_end_time', '_location', '_venue', '_privacy')
    readonly_fields = ('_graph', '_owner', '_name', '_description', '_start_time', '_end_time', '_location', '_venue', '_privacy', '_updated_time')
    list_display_links = ('id',)


class PageAdmin(AdminBase):
    def has_access(self, obj):
        return not (obj._access_token == None or obj._access_token == '')
    has_access.short_description = _('Access Token')
    has_access.boolean = True
    
    list_display = ('id', 'profile_link', 'slug', '_name', '_picture', '_likes', 'has_access')
    readonly_fields = ('_name', '_picture', '_likes', '_graph', '_link')
    actions = ['get_page_access_token']
    
    def get_page_access_token(self, request, queryset):
        graph = get_graph(request, force_refresh=True, prefer_cookie=True)
        response = graph.request('me/accounts/')   #&fields=id,access_token
        if response and response.get('data', False):
            data = response['data']
            message = {'count': 0, 'message': u''}
            accounts = {}
            for account in data:
                accounts[int(account['id'])] = account
            for page in queryset:
                if accounts.get(page._id, None):
                    if accounts[page._id].get('access_token', False):
                        queryset.filter(id=page._id).update(_access_token=accounts[page._id]['access_token'])
                        message['message'] = u'%sSet access token for page %s\n' % (message['message'], page._name)
                    else:
                        message['message'] = u'%sDid not get access token for page %s\n' % (message['message'], page._name)
                else:
                    message['message'] = u'%sYou are not admin for page %s\n' % (message['message'], page._name)
            self.message_user(request, '%s\n' % message['message'])
        else:
            self.message_user(request, 'There was an error: %s' % response )
    
    get_page_access_token.short_description = _('Get an access token for the selected page(s)')


class RequestAdmin(AdminBase):
    list_display = ('id', '_application_id', '_to', '_from', '_data', '_message', '_created_time')
    readonly_fields = ('_graph', '_application_id', '_to', '_from', '_data', '_message', '_created_time')




if hasattr(settings, 'FACEBOOK_ADMIN'):
    FACEBOOK_ADMIN = getattr(settings, 'FACEBOOK_ADMIN')
    if 'user' in FACEBOOK_ADMIN:
        admin.site.register(User, UserAdmin)
        if settings.DEBUG:
            admin.site.register(TestUser, UserAdmin)
    if 'page' in FACEBOOK_ADMIN:
        admin.site.register(Page, PageAdmin)
    if 'event' in FACEBOOK_ADMIN:
        admin.site.register(Event, EventAdmin)
    if 'request' in FACEBOOK_ADMIN:
        admin.site.register(Request, RequestAdmin)
    if 'score' in FACEBOOK_ADMIN:
        admin.site.register(Score, ScoreAdmin)
    if 'post' in FACEBOOK_ADMIN:
        admin.site.register(Post, PostAdmin)
    if 'photo' in FACEBOOK_ADMIN:
        admin.site.register(Photo, PhotoAdmin)

else:
    admin.site.register(User, UserAdmin)
    #admin.site.register(Photo, PhotoAdmin)
    #admin.site.register(Page, PageAdmin)
    #admin.site.register(Event, EventAdmin)
    #admin.site.register(Request, RequestAdmin)
    admin.site.register(Post, PostAdmin)

    if settings.DEBUG:
        admin.site.register(TestUser, UserAdmin)
