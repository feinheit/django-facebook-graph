from django.conf.urls.defaults import *

from views import redirect_to_slug

urlpatterns = patterns('',
    url(r'^$', redirect_to_slug, name='redirect_to_slug'),
)