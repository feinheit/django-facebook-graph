import re

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import views as auth_views
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from django.http import HttpResponseRedirect

import facebook

from registration import signals

@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    
    cookie = facebook.get_user_from_cookie(request.COOKIES, settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    
    # Because we override the login, we should check for POST data, to give priority to the django auth view
    if not request.method == "POST" and cookie:
        # Light security check -- make sure redirect_to isn't garbage.
        if not redirect_to or ' ' in redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL

        # Heavier security check -- redirects to http://example.com should 
        # not be allowed, but things like /view/?param=http://example.com 
        # should be allowed. This regex checks if there is a '//' *before* a
        # question mark.
        elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
                redirect_to = settings.LOGIN_REDIRECT_URL

        if not request.user.is_authenticated():
            new_user = authenticate(uid=cookie["uid"], access_token=cookie["access_token"])
            auth_login(request, new_user)
            signals.user_registered.send(sender='facebook_login',
                                     user=new_user,
                                     request=request)

        return HttpResponseRedirect(redirect_to)
    else:
        return auth_views.login(request, template_name, redirect_field_name, authentication_form)

def logout(request, next_page=None, template_name='registration/logged_out.html', redirect_field_name=REDIRECT_FIELD_NAME):
    cookie = facebook.get_user_from_cookie(request.COOKIES, settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET)
    response = auth_views.logout(request, next_page, template_name, redirect_field_name)
    if cookie:
        response.delete_cookie("fbs_" + settings.FACEBOOK_APP_ID)
    return response