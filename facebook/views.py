import sys, logging, urllib2
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden,\
    Http404
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404, render
from django.template import loader, RequestContext

from facebook.utils import validate_redirect
from facebook.graph import get_graph
from facebook.oauth2 import parseSignedRequest
from facebook.session import get_session
from facebook.modules.profile.application.utils import get_app_dict
from facebook.modules.profile.user.models import User


logger = logging.getLogger(__name__)

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
            user, created = User.objects.get_or_create(id=graph.user_id)
            user.get_from_facebook(request)
            user.access_token = graph.access_token
            user.save()

        return HttpResponse('ok')

    elif action == 'friends':
        if json == None:
            return HttpResponseBadRequest('Facebook Graph JSON response is required as "json" attribute')

        user, created = User.objects.get_or_create(id=graph.user_id)
        user.save_friends(json)

        return HttpResponse('ok')

    elif action == 'user-friends-once':
        user, created = User.objects.get_or_create(id=graph.user_id)
        if created or not user.access_token:
            user.get_friends(save=True, request=request)
        user.access_token = graph.access_token
        user.get_from_facebook(request)
        user.save()

        return HttpResponse('ok')

    return HttpResponseBadRequest('action %s not implemented' % action)



@csrf_exempt
def channel(request):
    """ Returns the channel.html file as described in http://developers.facebook.com/docs/reference/javascript/FB.init/"""
    fb = get_session(request)
    try:
        locale = fb.signed_request['user']['locale']
    except (AttributeError, KeyError, TypeError): # TODO really catch AttributeError too?
        locale = 'en_US'  #TODO: Make this nicer.
    t=datetime.now()+timedelta(weeks=500)
    response = HttpResponse(loader.render_to_string('facebook/channel.html', {'locale': locale},
                              context_instance=RequestContext(request)))
    response['Expires'] = t.ctime()
    return response


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
            logger.info('User %s asked for deauthorization. Not deleted in Debug mode.' % user)
        return HttpResponse('ok')
    raise Http404


@csrf_exempt
def parent_redirect(request):
    """ Forces a _parent redirect to the specified url. """
    
    encoded_url = request.GET.get('next','')
    unquoted_url = urllib2.unquote(encoded_url)
    
    if validate_redirect(unquoted_url):
        return render(request, 'facebook/redirecter.html', {'destination': unquoted_url })
    else:
        return HttpResponseForbidden('The next= paramater is not an allowed redirect url.')


@csrf_exempt
def internal_redirect(request):
    """ Forces a GET redirect. Use this if you do a parent redirect to your view
        if your view is csrf protected.
    """
    
    encoded_url = request.GET.get('page','')
    unquoted_url = urllib2.unquote(encoded_url)
    
    if validate_redirect(unquoted_url):
        return render(request, 'facebook/internalredirecter.html', {'destination': urllib2.unquote(unquoted_url) })
    else:
        return HttpResponseForbidden('The next= paramater is not an allowed redirect url.')


""" Allows to register client-side errors. """
def log_error(request):
    if not request.is_ajax() or not request.method == 'POST':
        raise Http404
    logger.error(request.POST.get('message'))
    return HttpResponse('logged error.')


def fql_console(request):
    if not settings.DEBUG:
        return HttpResponseForbidden
    else:
        return render_to_response('facebook/fqlconsole.html', {},
                                  RequestContext(request))


