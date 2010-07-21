import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from django.http import HttpResponseRedirect

import facebook
from facebook.models import FacebookUser

from registration import signals

@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    
    cookie = facebook.get_user_from_cookie(request.COOKIES, 
                                           settings.FACEBOOK_APP_ID, 
                                           settings.FACEBOOK_APP_SECRET)
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    
    # Because we override the login, we should check for POST data, 
    #to give priority to the django auth view
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
            new_user = authenticate(uid=cookie["uid"], 
                                    access_token=cookie["access_token"])
            auth_login(request, new_user)
            signals.user_registered.send(sender='facebook_login',
                                     user=new_user,
                                     request=request)

        return HttpResponseRedirect(redirect_to)
    else:
        return auth_views.login(request, template_name, 
                                redirect_field_name, authentication_form)

def logout(request, next_page=None, 
           template_name='registration/logged_out.html', 
           redirect_field_name=REDIRECT_FIELD_NAME):
    cookie = facebook.get_user_from_cookie(request.COOKIES, 
                                           settings.FACEBOOK_APP_ID, 
                                           settings.FACEBOOK_APP_SECRET)
    response = auth_views.logout(request, next_page, 
                                 template_name, redirect_field_name)
    if cookie:
        response.delete_cookie("fbs_" + settings.FACEBOOK_APP_ID)
    return response

def connect(request, redirect_field_name=REDIRECT_FIELD_NAME):
    cookie = facebook.get_user_from_cookie(request.COOKIES, 
                                           settings.FACEBOOK_APP_ID, 
                                           settings.FACEBOOK_APP_SECRET)
    redirect_to = request.REQUEST.get(redirect_field_name, reverse('account'))
    
    if request.user.is_authenticated() and cookie:
        try:
            graph = facebook.GraphAPI(cookie["access_token"])
            profile = graph.get_object("me")
        except facebook.GraphAPIError, e:
            return render_to_response(
                        'registration/facebook/graph_error.html', {'error': e},
                        context_instance=RequestContext(request))
        
        # if the user has already a facebook connection, abort and show
        # error message
        if hasattr(request.user, 'facebookuser'):
            connected_profile = graph.get_object("%s" % request.user.facebookuser.id)
            ctx = {'fb_name' : connected_profile['name'],
                   'fb_link' : connected_profile['link'],
                   'username' : request.user.username}
            return render_to_response(
                        'registration/facebook/already_connected.html', ctx,
                        context_instance=RequestContext(request))
        try:
            # if that facebook user already exists, abort and show error message
            fb_user = FacebookUser.objects.get(id=cookie['uid'])
            ctx = {'fb_name' : profile["name"],
                   'user' : fb_user.user}
            return render_to_response(
                        'registration/facebook/user_exists.html', ctx,
                        context_instance=RequestContext(request))
        except FacebookUser.DoesNotExist:
            fb_user = FacebookUser(id=cookie['uid'], 
                                   user=request.user,
                                   profile_url=profile["link"],
                                   access_token=cookie["access_token"])
            fb_user.save()
            return HttpResponseRedirect(redirect_to)
    
    elif request.user.is_authenticated():
        ctx = {'username' : request.user.username}
        # if no cookie is present, the user did not authorize the application
        # in facebook. show the facebook connect button
        return render_to_response('registration/facebook/connect.html', ctx,
                                  context_instance=RequestContext(request))
    else:
        # there is no facebook graph cookie and the user is not logged in
        # -> redirect to login page
        return HttpResponseRedirect(reverse('auth_login'))
