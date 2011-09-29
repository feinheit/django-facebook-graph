from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from models import User, Photo, Page, Event, Request, TestUser, Post, Score, Like
from utils import get_graph

def delete_object(modeladmin, request, queryset):
    graph = get_graph(request)
    for obj in queryset:
        obj.delete(graph=graph, facebook=True)
delete_object.short_description = _("Delete selected objects (also on Facebook)")


class AdminBase(admin.ModelAdmin):    
    search_fields = ['id']
    actions = [delete_object]
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
    
    list_display = ('icon_link', 'id', '_from', '_message', '_type', 'picture_link')
    list_display_links = ('id',)
    readonly_fields = ('_graph', '_application', '_to', '_from', '_message', '_picture', '_subject',
                       '_properties', '_actions', '_privacy', '_likes', '_comments', '_targeting')
    date_hierarchy = '_updated_time'
    list_filter = ('_type',)
    
    
admin.site.register(Post, PostAdmin)

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    readonly_fields = ('user', 'score')
    search_fields = ('user',)
    ordering = ['score']
    
""" Because Facebook does not yet correctly support score the score model is just experimental.
    Import it in your project admin file:
    
    from facebook.models import Score
    from facebook.admin import ScoreAdmin
    admin.site.register(Score, ScoreAdmin)
"""

class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', '_name', '_category')
    search_fields = ('user', '_name')
    ordering = ['user', '_created_time']
    
admin.site.register(Like, LikeAdmin)




