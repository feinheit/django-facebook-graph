from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from facebook.graph import get_graph, GraphAPIError

import logging, datetime
from django.utils import timezone
from facebook.modules.profile.application.utils import get_app_dict
from facebook.utils import do_exchange_token

logger = logging.getLogger(__name__)

from django.conf import settings
from facebook.modules.profile.models import ProfileAdmin

from .models import Page

class PageAdmin(ProfileAdmin):
    def has_access(self, obj):
        if obj.updated + datetime.timedelta(days=60) < timezone.now():
            # Token expired unless the page still has a never-expiring token.
            return False
        return not (obj._access_token == None or obj._access_token == '')
    has_access.short_description = _('Access Token')
    has_access.boolean = True

    def token_expires_in(self, obj):
        if not obj._access_token_expires:
            return ''
        expires_in = (obj._access_token_expires - datetime.datetime.now()).days
        if expires_in > 10:
            return _('%s days' % expires_in)
        elif expires_in < 0:
            return _('<span style="color:red;font-weight:bold;">expired</span>')
        else:
            return _('<span style="color:orange;font-weight:bold;">%s days</span>' % expires_in)

    token_expires_in.short_description = _('expires in')
    token_expires_in.allow_tags = True

    def insight_link(self, obj):
        if '?' in obj.facebook_link:
            return u'<a href="%s&sk=page_insights" target="_blank">%s</a>' % (obj.facebook_link, obj._name)
        else:
            return u'<a href="%s?sk=page_insights" target="_blank">%s</a>' % (obj.facebook_link, obj._name)
    insight_link.allow_tags = True
    insight_link.short_description = _('Name')


    list_display = ('id', 'profile_link', 'slug', 'insight_link', 'pic_img',
                    '_likes', 'has_access', 'token_expires_in', 'updated')
    readonly_fields = ('_name', '_picture', '_likes', '_graph', '_link',
                       '_location', '_phone', '_checkins', '_website',
                       '_talking_about_count','_username', '_category')
    actions = ['get_page_access_token']

    def get_page_access_token(self, request, queryset):
        default_post_app = getattr(settings, 'DEFAULT_POST_APP', None)
        graph = get_graph(request, app_name=default_post_app, force_refresh=True, prefer_cookie=True)
        app_dict = get_app_dict(default_post_app)
        token_exchange = do_exchange_token(app_dict, graph.access_token)
        logger.debug('exchanged token: %s' % token_exchange)
        token_expires_in = datetime.timedelta(minutes=60)
        if 'access_token' in token_exchange:
            graph.access_token = token_exchange['access_token']
            token_expires_in = datetime.timedelta(days=60)
        try:
            response = graph.request('me/accounts/')
        except GraphAPIError as e:
            self.message_user(request, 'There was an error: %s' % e.message )
            return False
        #logger.debug(response)
        token_expires_in = datetime.datetime.now() + token_expires_in
        if response and response.get('data', False):
            data = response['data']
            message = {'count': 0, 'message': u''}
            accounts = {}
            for account in data:
                accounts[int(account['id'])] = account
            for page in queryset:
                if accounts.get(page._id, None):
                    if accounts[page._id].get('access_token', False):
                        queryset.filter(id=page._id).update(_access_token=accounts[page._id]['access_token'],
                                                            _access_token_expires=token_expires_in)
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