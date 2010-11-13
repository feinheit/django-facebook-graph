import logging
logger = logging.getLogger(__name__)

import facebook
import urllib

from django.conf import settings
from django.utils import simplejson

_parse_json = lambda s: simplejson.loads(s)

def get_graph(request=None, access_token=None, client_secret=None, client_id=None):
    """ Tries to get a facebook graph by different methods.
    
    * via access_token: that one is simple
    * via request cookie (access token)
    * via application -> make an accesstoken for an application
    
    """
    
    # if no application is specified, get default from settings
    if not client_secret: client_secret = settings.FACEBOOK_APP_SECRET
    if not client_id: client_id = settings.FACEBOOK_APP_ID
    
    if access_token:
            graph = facebook.GraphAPI(access_token)
            graph.via = 'access_token'
            logger.debug('got graph via access_token: %s' % graph.access_token)
            return graph
    
    if request:
        cookie = facebook.get_user_from_cookie(request.COOKIES, client_id, client_secret)
        
        if cookie != None:
            graph = facebook.GraphAPI(cookie["access_token"])
            graph.user = cookie['uid']
            graph.via = 'cookie'
            logger.debug('got graph via cookie. access_token: %s' % graph.access_token) 
            return graph
        else:
            logger.debug('could not get graph via cookie. cookies: %s' % request.COOKIES)
    
    # get token by application
    file = urllib.urlopen('https://graph.facebook.com/oauth/access_token?%s' 
                          % urllib.urlencode({'type' : 'client_cred',
                                              'client_secret' : client_secret,
                                              'client_id' : client_id}))
    raw = file.read()
    
    try:
        response = _parse_json(raw)
        if response.get("error"):
            raise facebook.GraphAPIError(response["error"]["type"],
                                         response["error"]["message"])
        else:
            raise facebook.GraphAPIError('GET_GRAPH', 'Facebook returned json (%s), expected access_token' % response)
    except:
        # if the response ist not json, it is 
        access_token = raw.split('=')[1]
    finally:
        file.close()
    
    graph = facebook.GraphAPI(access_token)
    graph.via = 'application'
    logger.debug('got graph via application: %s. access_token: %s' %(client_id, graph.access_token)) 
    return graph
    

