from django.conf.urls.defaults import *

from views import input

urlpatterns = patterns('',
    url(r'^(?P<action>[a-z-]+)/$', input, name="input"),
)