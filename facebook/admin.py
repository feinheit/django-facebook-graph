from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from facebook.graph import get_graph
#from facebook import FbPhoto, FbPost, FbUser, FbTestUser, FbPage, \
#                     FbEvent, FbRequest, FbScore


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
            return '<a href="%s" target="_blank"><img src="%s/picture?type=square" /></a>'\
                 % (obj.facebook_link, obj.graph_url)
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

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    readonly_fields = ('user', 'score')
    search_fields = ('user',)
    ordering = ['score']


    

if hasattr(settings, 'FACEBOOK_ADMIN'):
    FACEBOOK_ADMIN = getattr(settings, 'FACEBOOK_ADMIN')
    if 'user' in FACEBOOK_ADMIN:
        admin.site.register(FbUser, UserAdmin)
    if 'page' in FACEBOOK_ADMIN:
        admin.site.register(FbPage, PageAdmin)
    if 'event' in FACEBOOK_ADMIN:
        admin.site.register(FbEvent, EventAdmin)
    if 'request' in FACEBOOK_ADMIN:
        admin.site.register(FbRequest, RequestAdmin)
    if 'score' in FACEBOOK_ADMIN:
        admin.site.register(FbScore, ScoreAdmin)
    if 'post' in FACEBOOK_ADMIN:
        admin.site.register(FbPost, PostAdmin)
    if 'photo' in FACEBOOK_ADMIN:
        admin.site.register(FbPhoto, PhotoAdmin)

#else:
    #admin.site.register(FbUser, UserAdmin)
    #admin.site.register(FbPhoto, PhotoAdmin)
    #admin.site.register(FbPage, PageAdmin)
    #admin.site.register(FbEvent, EventAdmin)
    #admin.site.register(FbRequest, RequestAdmin)
    #admin.site.register(FbPost, PostAdmin)

#if settings.DEBUG:
#    admin.site.register(FbTestUser, UserAdmin)
