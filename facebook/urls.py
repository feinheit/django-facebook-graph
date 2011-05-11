from django.conf.urls.defaults import *

from views import input
from django.views.generic.simple import direct_to_template
from django.views.decorators.csrf import csrf_exempt


""" Use this instead of direct_to_template """
go_to_template = csrf_exempt(direct_to_template)


urlpatterns = patterns('',
    url(r'^deauthorize/$', 'facebook.views.deauthorize_and_delete', name='deauthorize'),
    url(r'^(?P<action>[a-z-]+)/$', input, name="input"),
)