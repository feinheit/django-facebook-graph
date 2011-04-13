import logging
logger = logging.getLogger(__name__)

import cgi
import urllib

from django.conf import settings
from django.shortcuts import redirect
from django.utils import simplejson

_parse_json = lambda s: simplejson.loads(s)

from utils import parseSignedRequest


class OAuth2ForCanvasMiddleware(object):
    def process_request(self, request):
        """
        Writes in the Session the signed_request
        """
        facebook = request.session.get('facebook', dict())
        app_secret = settings.FACEBOOK_APP_SECRET
        application = None
        
        # if feincms is installed, try to get the application from the page
        try:
            from facebook.feincms.utils import get_application_from_request
            application = get_application_from_request(request)
            if application:
                app_secret = application.secret
        except ImportError:
            logger.debug('FeinCMS not installed')
        
        # default POST/GET request from facebook with a signed request
        if 'signed_request' in request.REQUEST:
            facebook['signed_request'] = parseSignedRequest(request.REQUEST['signed_request'], app_secret)
            logger.debug('got signed_request from facebook: %s' % facebook['signed_request'])
            
            if facebook['signed_request'].get('oauth_token', None):
                facebook['access_token'] = facebook['signed_request']['oauth_token']
        
        # auth via callback from facebook
        if 'code' in request.REQUEST:
            args = dict(client_id=settings.FACEBOOK_APP_ID,
                        client_secret=settings.FACEBOOK_APP_SECRET,
                        code=request.GET['code'],
                        redirect_uri = request.build_absolute_uri()
                            .split('?')[0]
                            .replace(settings.FACEBOOK_CANVAS_URL, settings.FACEBOOK_CANVAS_PAGE)
                        )
            
            response = urllib.urlopen("https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args))
            raw = response.read()
            parsed = cgi.parse_qs(raw)
            
            if parsed.get('access_token', None):
                facebook['access_token'] = parsed["access_token"][-1]
                logger.debug('got access_token from facebook callback: %s' % facebook['access_token'])
            else:
                logger.warning('facebook did not respond an accesstoken: %s' % raw)
        
        # old (?) method where facebook serves the accestoken unencrypted in 'session' parameter
        if 'session' in request.REQUEST:
            session = _parse_json(request.REQUEST['session'])
            facebook['access_token'] = session.get('access_token')
            logger.debug('got access_token from session: %s' % request.REQUEST['session'])
        
        request.session['facebook'] = facebook


class Redirect2AppDataMiddleware(object):
    """ If app_data is specified, this middleware assumes that app_data is the deep link and redirects to that page 
    example: http://www.facebook.com/PAGENAME?sk=app_APP_ID&app_data=/foo/bar/ redirects to /foo/bar/
    /
    IMPLEMENTATION: this middleware should be placed after OAuth2ForCanvasMiddleware, because it needs session['facebook']
    """
    
    def process_request(self, request):
        try:
            # only execute first time (Facebook will POST the tab with signed_request parameter)
            if request.method == 'POST' and request.POST.has_key('signed_request'):
                target_url = request.session['facebook']['signed_request']['app_data']
                return redirect(target_url)
            else:
                return None
        except KeyError:
            return None


class FakeSessionCookieMiddleware(object):
    # from http://djangosnippets.org/snippets/460/
    def process_request(self, request):
        """ tries to get the session variable via HTTP GET if there is no cookie """
        if not request.COOKIES.has_key(settings.SESSION_COOKIE_NAME) \
            and request.REQUEST.has_key(settings.SESSION_COOKIE_NAME):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = \
              request.REQUEST[settings.SESSION_COOKIE_NAME]
            request.COOKIES['fakesession'] = True
    
    def process_response(self, request, response):
        cookie_name = settings.SESSION_COOKIE_NAME
        
        if isinstance(response, (HttpResponseRedirect, HttpResponsePermanentRedirect)):
            location = response._headers['location'][1]
            
            # only append session id if the redirection stays inside (local)
            if not location.find('http') == 0:
                separator = '&' if '?' in location else '?'
                response._headers['location'] = ('Location' , '%s%s%s=%s' % (location, 
                            separator, cookie_name, 
                            request.session._get_session_key()))
            
                logger.debug('FakeSessionCookieMiddleware: changed redirect location from "%s" to "%s" ' % (location, response._headers['location'][1]))
        return response

