import logging
logger = logging.getLogger(__name__)

import cgi
import urllib

from django.conf import settings
from django.utils import simplejson

_parse_json = lambda s: simplejson.loads(s)

from utils import parseSignedRequest


class OAuth2ForCanvasMiddleware(object):
    def process_request(self, request):
        """
        Writes in the Session the signed_request
        """
        facebook = request.session.get('facebook', dict())
        
        if request.REQUEST.get('signed_request', None):
            facebook['signed_request'] = parseSignedRequest(request.REQUEST['signed_request'])
            logger.debug('got signed_request from facebook: %s' % facebook['signed_request'])
            
            if facebook['signed_request'].get('oauth_token', None):
                facebook['access_token'] = facebook['signed_request']['oauth_token']
        
        if request.REQUEST.get('code', None):
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
        
        if request.REQUEST.get('session'):
            session = _parse_json(request.REQUEST['session'])
            facebook['access_token'] = session.get('access_token')
            logger.debug('got access_token from session: %s' % request.REQUEST['session'])
        
        request.session['facebook'] = facebook

