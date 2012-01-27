from django.contrib import admin

from facebook.modules.base import AdminBase

from .models import Page


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