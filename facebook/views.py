from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.conf import settings
from facebook.utils import get_graph, parseSignedRequest, get_app_dict
import functools, sys, logging
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import urlencode
from django.core.urlresolvers import resolve, Resolver404, reverse
from django.contrib.sites.models import Site
from feinheit.newsletter.models import Subscription
from feinheit.translations import short_language_code

logger = logging.getLogger(__name__)

from models import User

runserver = ('runserver' in sys.argv)

def input(request, action):
    """ method to save a graph-object query, that is retrieved client side """
    
    json = request.POST.get('json', None)
    
    graph = get_graph(request)
    
    if action == 'user':
        if json:
            user, created = User.objects.get_or_create(id=json['id'])
    
            user.access_token = graph.access_token
            user.save_from_facebook(json)
        else:
            user, created = User.objects.get_or_create(id=graph.user)
            user.get_from_facebook(request)
            user.access_token = graph.access_token
            user.save()
        
        return HttpResponse('ok')
    
    elif action == 'friends':
        if json == None:
            return HttpResponseBadRequest('Facebook Graph JSON response is required as "json" attribute')
        
        user, created = User.objects.get_or_create(id=graph.user)
        user.save_friends(json)
        
        return HttpResponse('ok')
    
    elif action == 'user-friends-once':
        user, created = User.objects.get_or_create(id=graph.user)
        if created or not user.access_token:
            user.get_friends(save=True, request=request)
        user.access_token = graph.access_token
        user.get_from_facebook(request)
        user.save()
        
        return HttpResponse('ok')
    
    return HttpResponseBadRequest('action %s not implemented' % action)

"""
try:
    page_id = settings.FACEBOOK_PAGE_ID
except AttributeError:
    raise ImproperlyConfigured, 'You have to define FACEBOOK_PAGE_ID in your settings!'
try:
    redirect_url = settings.FACEBOOK_REDIRECT_PAGE_URL
except AttributeError:
    raise ImproperlyConfigured, 'You have to define FACEBOOK_REDIRECT_PAGE_URL in your settings!\n'\
            'i.e. http://www.facebook.com/#!/myapp'
try:
    app_id = settings.FACEBOOK_APP_ID
except AttributeError:
    raise ImproperlyConfigured, 'You have to define FACEBOOK_APP_ID in your settings!'
"""

def redirect_to_page(view):   
    """ Decorator that redirects a canvas URL to a page using the path that is in app_data.path """
    """ Decorate the views where you have links to the app page. """
    
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        request = args[0]
        # if this is already the callback, do not wrap.
        if getattr(request, 'avoid_redirect', False):
            logger.debug('entered calback. View: %s, kwargs: %s' %(view, kwargs))
            return view(*args, **kwargs)
        
        session = request.session.get('facebook', dict())
        try:
            signed_request = session['signed_request']
        except KeyError:
            logger.debug('No signed_request in current session. Returning View.')
            return view(*args, **kwargs)
            
        logger.debug('signed_request: %s' %signed_request)
        
        if 'app_data' in signed_request:
            app_data = signed_request['app_data']
            del request.session['facebook']['signed_request']['app_data']
            request.session.modified = True
            logger.debug('found app_data url: %s' %app_data)
            #return HttpResponseRedirect(app_data)
            try:
                original_view = resolve(app_data)
            except Resolver404:
                logger.debug('Did not find view for %s.' %app_data)
                url = u'%s?sk=app_%s' % (redirect_url, app_id)
                return render_to_response('redirecter.html', {'destination': url }, RequestContext(request)) 
                
            logger.debug('found original view url: %s' %original_view)
            setattr(request, 'avoid_redirect' ,  True)
            # call the view that was originally requested:
            return original_view.func(request, *original_view.args, **original_view.kwargs)
        else:
            #check if the app is inside the specified page.
            try:
                page = signed_request['page']['id']
            except KeyError:
                page = None
            if page <> page_id and not runserver:
                logger.debug('Tab is not in original Page. Redirecting...')
                url = u'%s?sk=app_%s&app_data=%s' % (redirect_url, app_id, urlencode(request.path))
                return render_to_response('redirecter.html', {'destination': url }, RequestContext(request))        
            
        return view(*args, **kwargs)
    
    return wrapper

# Deauthorize callback, signed request: {u'issued_at': 1305126336, u'user_id': u'xxxx', u'user': {u'locale': u'de_DE', u'country': u'ch'}, u'algorithm': u'HMAC-SHA256'}

@csrf_exempt
def deauthorize_and_delete(request):
    """ Deletes a user on a deauthorize callback. """
    if request.method == 'GET':
        raise Http404
    if 'signed_request' in request.POST:
        application = get_app_dict()
        parsed_request = parseSignedRequest(request.REQUEST['signed_request'], application['SECRET'])
        user = get_object_or_404(User, id=parsed_request['user_id'])
        if settings.DEBUG == False:
            user.delete()
            logger.info('Deleting User: %s' % user)
        else:
            logger.info('User %s asked for deauthorization. Not deleted in Debug mode.')
        return HttpResponse('ok')
    raise Http404

