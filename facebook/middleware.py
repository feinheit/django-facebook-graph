import logging
logger = logging.getLogger(__name__)

import cgi
import urllib

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.utils import simplejson, translation

_parse_json = lambda s: simplejson.loads(s)

from utils import parseSignedRequest


class OAuth2ForCanvasMiddleware(object):
    def process_request(self, request):
        """
        Writes the signed_request into the Session 
        """
        fb = request.session.get('facebook', dict())
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
            fb['signed_request'] = parseSignedRequest(request.REQUEST['signed_request'], app_secret)
            logger.debug('got signed_request from facebook: %s' % fb['signed_request'])
            language = fb['signed_request']['user']['locale']
            logger.debug('language: %s' %language)
            request.LANGUAGE_CODE = language
            translation.activate(language)
            
            # rewrite important data
            if 'oauth_token' in fb['signed_request']:
                fb['access_token'] = fb['signed_request']['oauth_token']
            if 'access_token' in fb['signed_request']:
                fb['access_token'] = fb['signed_request']['access_token']
            if 'user_id' in fb['signed_request']:
                fb['user_id'] = fb['signed_request']['user_id']
                fb['app_is_authenticated'] = True
            request.session['facebook'] = fb
            request.session.modified = True
        # auth via callback from facebook
        elif 'code' in request.REQUEST:
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
                fb['access_token'] = parsed["access_token"][-1]
                logger.debug('got access_token from facebook callback: %s' % fb['access_token'])
            else:
                logger.debug('facebook did not respond an accesstoken: %s' % raw)
            request.session['facebook'] = fb
            request.session.modified = True
        # old (?) method where facebook serves the accestoken unencrypted in 'session' parameter
        elif 'session' in request.REQUEST:
            session = _parse_json(request.REQUEST['session'])
            fb['access_token'] = session.get('access_token')
            logger.debug('got access_token from session: %s' % request.REQUEST['session'])
            request.session['facebook'] = fb
            request.session.modified = True
        
        


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
            if not location.find('http') == 0 and not location.find('/admin/') == 0:
                separator = '&' if '?' in location else '?'
                response._headers['location'] = ('Location' , '%s%s%s=%s' % (location, 
                            separator, cookie_name, 
                            request.session._get_session_key()))
            
                logger.debug('FakeSessionCookieMiddleware: changed redirect location from "%s" to "%s" ' % (location, response._headers['location'][1]))
        return response

