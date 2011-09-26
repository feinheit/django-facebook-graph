import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

from django.http import HttpResponseRedirect, HttpResponse

import facebook
from facebook.models import User as FacebookUser
from facebook.utils import get_app_dict, get_graph, get_session

import logging
logger = logging.getLogger(__name__)


@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          app_name=None):
    
    fb_app=get_app_dict(app_name)
    
    graph = get_graph(request, app_name=app_name)

    redirect_to = request.REQUEST.get(redirect_field_name, '')

    # Because we override the login, we should check for POST data,
    #to give priority to the django auth view
    if not request.method == "POST":
        # Light security check -- make sure redirect_to isn't garbage.
        if not redirect_to or '' in redirect_to:
            redirect_to = fb_app['REDIRECT-URL']
        
        """
        # TODO: Check only if the domain is in 'DOMAIN' or 'facebook.com' but without the protocol
        
        elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
                redirect_to = fb_app['REDIRECT-URL']
        """
                        
        new_user = authenticate(graph=graph)
        logger.debug('new user: %s' %new_user)

        # Authentication might still fail -- new_user might be an
        # instance of AnonymousUser.
        if new_user and new_user.is_authenticated():
            auth_login(request, new_user)

            if 'registration' in settings.INSTALLED_APPS:
                from registration import signals
                signals.user_registered.send(sender='facebook_login',
                                         user=new_user,
                                         request=request)

        return redirect(redirect_to)
    
    logger.debug('could not login user %s' % graph.user_id)
    return auth_views.login(request, template_name,
                            redirect_field_name, authentication_form)


def logout(request, next_page=None,
           template_name='registration/logged_out.html',
           redirect_field_name=REDIRECT_FIELD_NAME):
    
    fb_app=get_app_dict()  # TODO: Make this multi-app capable. Add app to login-url.
    fb_session = get_session(request)
    
    fb_session.store_token(None)
    
    response = auth_views.logout(request, next_page,
                                 template_name, redirect_field_name)

    # This might lead to unexpected results with multiple apps. 
    response.delete_cookie("fbsr_" + fb_app['ID'])
    
    redirect_to = next_page or request.REQUEST.get(redirect_field_name, '')
    if not redirect_to or ' ' in redirect_to:
        redirect_to = fb_app['REDIRECT-URL']
    
    return redirect(redirect_to)


def connect(request, redirect_field_name=REDIRECT_FIELD_NAME, app_name=None):
    """ Connects the Facebook Account to the current logged-in user. """
    fb_app = get_app_dict(app_name)
    graph = get_graph(request, app_name=app_name)
    redirect_to = request.REQUEST.get(redirect_field_name, fb_app['REDIRECT-URL'])

    if request.user.is_authenticated():
        try:
            me = graph.get_object("me")
        except facebook.GraphAPIError as e:
            return redirect('fb_login')

        # if the user has already a facebook connection, abort and show
        # error message
        if hasattr(request.user, 'user'):
            logger.debug('The logged in user is already connected.')
            # check if the django user and FB user match:
            if graph.user_id <> request.user.user.id:
                logger.debug('User %s already connected with Facebook account %s' % (request.user.get_full_name, request.user.user._name))
                auth_views.logout(request, next_page=reverse('fb_app'))
            # Otherwise redirect
            return redirect(redirect_to)
        else:
            # The User has no Facebook account attached. Connect him. 
            try:
                # if that facebook user already exists, abort and show error message
                fb_user = FacebookUser.objects.get(id=graph.user_id)
            except FacebookUser.DoesNotExist:
                fb_user = FacebookUser(id=graph.user_id)
                fb_user.get_from_facebook(graph=graph, save=True)
            else:
                if isinstance(fb_user.user, User):
                    auth_views.logout(request, next_page=reverse('fb_login'))
                else:
                    fb_user.user = request.user
                    fb_user.save()
            finally:
                return redirect(redirect_to)

    else:
        # The user is not logged in
        # -> redirect to login page
        return redirect('fb_login')
