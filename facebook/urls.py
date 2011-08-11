from django.conf.urls.defaults import *

from views import input
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt


""" Use this instead of direct_to_template """
go_to_template = csrf_exempt(TemplateView.as_view)


urlpatterns = patterns('',
    url(r'^deauthorize/$', 'facebook.views.deauthorize_and_delete', name='deauthorize'),
    url(r'^fql/$', 'facebook.views.fql_console', name="fql_console"),
    url(r'^log_error/$', 'facebook.views.log_error', name="log_error"),
    url(r'^channel.html$', 'facebook.views.channel', name='channel'),
    url(r'^redirect/$', 'facebook.views.redirect', name='fb-redirect'),
    url(r'^(?P<action>[a-z-]+)/$', input, name="input"),
)

