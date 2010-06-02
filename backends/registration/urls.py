from django.conf.urls.defaults import *

from views import login, logout

urlpatterns = patterns('',
                       url(r'^login/$', 
                           login,
                           {'template_name': 'registration/login.html'},
                           name='auth_login'),
                       url(r'^logout/$',
                           logout,
                           {'template_name': 'registration/logout.html'},
                           name='auth_logout'),
                       (r'', include('registration.auth_urls')),
                       )