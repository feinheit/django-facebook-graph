import logging
import warnings
import urlparse
logger = logging.getLogger(__name__)


import itertools
import mimetools
import mimetypes

import urllib
import urllib2
import urlparse

import facebook

from django.conf import settings
from django.shortcuts import redirect
from django.utils import simplejson
from django.utils.http import urlquote

from datetime import datetime, timedelta

from api import base64_url_decode

from facebook.api import parseSignedRequest

# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)

import logging
logger = logging.getLogger(__name__)

"""
Example App Settings Entry:

FACEBOOK_APPS = {
    'My great App' : {
            'ID': '155XXXXXXXXXXX',
            'API-KEY': 'depreciated: same as ID',
            'SECRET': 'cbXXXXXXXXXXXXXXXXXXXXXd8',
            'CANVAS-PAGE': 'http://apps.facebook.com/mygreatapp/',
            'CANVAS-URL': 'http://localhost.local/',
            'SECURE-CANVAS-URL': 'https://localhost.local/',
            'REDIRECT-URL': 'http://apps.facebook.com/mygreatapp/',
            'DOMAIN': 'http://localhost.local:8000',
    }
}

"""
# TODO: Check if protocol relative URLs work or put the protocol for the redirect URL elswhere.



def get_app_dict(application=None):
    if not application:
        if getattr(settings, 'FACEBOOK_DEFAULT_APPLICATION', False):
            application = settings.FACEBOOK_APPS[settings.FACEBOOK_DEFAULT_APPLICATION]
        else:
            application = settings.FACEBOOK_APPS.values()[0]
    else:
        application = settings.FACEBOOK_APPS[application]
    return application


def authenticate(code, app_id, app_secret, redirect_uri=""):
    access_token = None
    
    args = {'client_id': app_id,
            'client_secret': app_secret,
            'code': code.replace("\"", ""),
            'redirect_uri': redirect_uri
            }  
    file = urllib.urlopen("https://graph.facebook.com/oauth/access_token?" + urllib.urlencode(args))
    raw = file.read()
    file.close()
    logger.debug('Got Graph Response: %s' % raw)
    # The raw response is a urlparsed string (access_token=xxxxxxxx&expires=6295).
    # We convert it to a dict.
    response = urlparse.parse_qs(raw)
    
    if response == {}:
        # An error occured: The response is a JSON string containing the error.
        try:
            response = _parse_json(raw)
        except ValueError:
            raise facebook.GraphAPIError('AUTHENTICATION ERROR', 'Facebook returned this: %s. Expected access token.' % raw)
        else:
            if isinstance(response, dict) and response.get("error"):
                # The Code is invalid. Maybe the user logged out of Facebook or removed the app.
                raise facebook.GraphAPIError(response["error"]["type"],
                                             response["error"]["message"])
            else:
                raise facebook.GraphAPIError('AUTHENTICATION ERROR', 'Facebook returned json (%s), expected access_token' % response)
        
    logger.debug('Authentication Graph Response: %s' % response)
    return response


"""
def get_REST(method, params):
    query = 'https://api.facebook.com/method/%s?format=json&%s' % (method, urllib.urlencode(params))
    file = urllib.urlopen(query)
    raw = file.read()

    logger.debug('facebook REST response raw: %s, query: %s' % (raw, query))

    try:
        response = _parse_json(raw)
    except:
        response = {'response': raw}
    finally:
        file.close()

    return response
"""

def get_FQL(fql, access_token=None):
    query = 'https://api.facebook.com/method/fql.query?format=json'

    params = {'query': fql}

    if access_token:
        params.update({'access_token': access_token})

    file = urllib.urlopen(query, urllib.urlencode(params))
    raw = file.read()

    logger.debug('facebook FQL response raw: %s, query: %s, FQL: %s' % (raw, query, fql))

    try:
        response = _parse_json(raw)
    finally:
        file.close()
    if isinstance(response, dict) and response.get('error_code', False):
        raise facebook.GraphAPIError(response['error_code'], response['error_msg'])
    return response

class SessionBase(object):    
    def __init__(self):
        self.app_is_authenticated, self.access_token, self.signed_request = True, None, None
        self.token_expires, self.user_id, self.me = None, None, None
        self.app_requests = []  # TODO: Put this in its own class.
    
    def store_token(self, *args, **kwargs):
        raise AttributeError('Not Implemented')
    
    def modified(self):
        raise AttributeError('Not Implemented')
    
    class Meta:
        abstract=True

    
class FBSession(SessionBase):
    """ This class uses Properties and setter. Requires Python 2.6. """    
    def __init__(self, request):
        if request == None:
            raise AttributeError('Need Request to Access the Session.')
        if hasattr(request, 'fb_session'):
            raise AttributeError('Session already exists in Request.')
        self.fb_session = self.get_fb_session(request)
        self.request = request
    
    def get_fb_session(self, request):
        fb = request.session.get('facebook', None)
        logger.debug('found facebook session')
        if not fb:
            logger.debug('did not find a facebook session. Creating a new one.')
            request.session.update({'facebook': {'app_is_authenticated': True}})
            request.session.modified = True
            fb = request.session['facebook']
        return fb
    
    def modified(self, who='unknown'):
        self.request.session.modified = True
        logger.debug('Session modified by %s: %s' % (who, self.fb_session))
            

    # DEPRECATED FUNCTION:
    # Maybe change this so it returns at least the user_id.
    def cookie_info(self, app_dict, store=True):
        graph = get_graph(self.request, app_dict=app_dict)
        cookie = graph.get_user_from_cookie()
        if cookie:
            if store:
                if cookie['uid']:
                    self.fb_session['user_id'] = cookie['uid']
                if cookie['access_token']:
                    self.access_token = cookie['access_token']
            return {'user_id': cookie['uid'], 'access_token': cookie['access_token']}
        else:
            return None

    
    @property
    def app_is_authenticated(self):
        """This is a cached value to store if the app is authenticated. """
        return self.fb_session['app_is_authenticated'] \
               if self.fb_session.get('app_is_authenticated', False) else True  # Assuming True.
    
    @app_is_authenticated.setter
    def app_is_authenticated(self, status):
        if status in [True, False]:
            self.fb_session['app_is_authenticated'] = status
        else:
            raise TypeError('FBSESSION', 'Authenticated takes True or False, not %s.' %status)
        
    @property
    def access_token(self):
        """ Returns the current access token or None. """
        logger.debug('token expires: %s, type: %s' % (self.token_expires, type(self.token_expires)))
        if self.token_expires and self.token_expires < datetime.now():  # TODO: Check if this is executed on every request.
            logger.debug('not returning expired access_token. %s' % self.fb_session.get('access_token'))
            return None
        else:
            return self.fb_session.get('access_token', None)
    
    @access_token.setter
    def access_token(self, token):
        self.fb_session['access_token'] = token
        self.modified('access_token.setter')
    
    @property
    def token_expires(self):
        return self.fb_session.get('access_token_expires', None)
    
    # expires can be datetime or None (i.e. an Application token has no known expiration date.
    @token_expires.setter
    def token_expires(self, expires):
        if isinstance(expires, datetime) or isinstance(expires, type(None)):
            logger.debug('token expires: %s' % expires)
            self.fb_session['access_token_expires'] = expires
            self.modified('token_expires setter')  # Is usually used with token setter.
        else:
            raise TypeError('Token Expires requires a datetime instance or None. Got %s instead.' %type(expires))        
    
    def store_token(self, token=None, expires=None):
        if token == None:
            self._clear_token()
        else:
            self.access_token = token
            if not expires:
                expires=datetime.now() + timedelta(hours=1)
            self.token_expires = expires
    
    def _clear_token(self):
        self.access_token = None
        self.user_id = None
        self.app_is_authenticated = False      

    
    @property
    def user_id(self):
        user_id = self.fb_session.get('user_id')
        return int(user_id) if user_id else None
    
    @user_id.setter
    def user_id(self, id):
        if id == None:
            self.fb_session['user_id'] = None
            self.fb_session['me'] = None
            self.app_is_authenticated = False
        else:
            self.fb_session['user_id'] = id
            self.app_is_authenticated = True
        self.modified('user_id.setter')
    
    @property
    def me(self):
        return self.fb_session.get('me', None)
    
    @me.setter
    def me(self, value):
        self.fb_session['me'] = value
        self.app_is_authenticated = True
        self.modified('me.setter')
    
    @property
    def signed_request(self):
        return self.fb_session.get('signed_request', None)
    
    @signed_request.setter
    def signed_request(self, parsed_request):
        self.fb_session['signed_request'] = parsed_request
        self.app_is_authenticated = True if getattr(parsed_request, 'user_id', False) else False
        self.modified('signed_request.setter')
    
    @property
    def user(self):
        raise AttributeError('The user attribute was confusing.\n Use signded_request["user"] instead.' )
    
    @user.setter
    def user(self, user):
        raise AttributeError('The user attribute was confusing.\n Use signded_request["user"] instead.' )

    @property
    def app_requests(self):
        ar = self.fb_session.get('app_requests', None)
        return ar.split(',') if ar else []
    
    @app_requests.setter
    def app_requests(self, item):
        if isinstance(item, list):
            self.fb_session['app_requests'] = ','.join(str(i) for i in item)
        elif isinstance(item, facebook.models.Request):
            ar = self.fb_session.get('app_requests', []).split(',')
            ar.append(str(item.id))
            self.fb_session['app_requests'] = ','.join(ar)
        elif isinstance(item, (basestring, int)):
            ar = self.fb_session.get('app_requests', []).split(',')
            ar.append(str(item))
            self.fb_session['app_requests'] = ','.join(ar)
        else:
            raise AttributeError, 'App_Requests must be a list, Request, str or int, not %s' %type(item)
        self.modified('app_requests.setter')
        
class FBSessionNoOp(SessionBase):
    def __init__(self):
        super(FBSessionNoOp, self).__init__()
        logger.debug('Using Dummy Session Interface')
        self._modified = False
    
    def store_token(self, token=None, expires=None):
        self.access_token = token
        self.token_expires = expires
    
    def modified(self, who='Unknown', *args, **kwargs):
        self._modified = True
        logger.debug('%s is trying to modify a dummy session.' % who )
        return False
    

class Graph(facebook.GraphAPI):
    """ The Base Class for a Facebook Graph. Inherits from the Facebook SDK Class. """
    """ Tries to get a facebook graph using different methods.
    * via access_token: that one is simple
    * via request cookie (access token)
    * via application -> create an accesstoken for an application if requested.
    Needs OAuth2ForCanvasMiddleware to deal with the signed Request and Authentication code.
    Put any graph.get_... calls in a try except structure. An Access Token might be invalid.
    In that case a GraphAPIError is raised.
    
    """
    def __init__(self, app_dict, request=None, access_token=None, 
                 code=None, request_token=True, force_refresh=False,
                 prefer_cookie=False):
        super(Graph, self).__init__(access_token)  # self.access_token = access_token
        logger.debug('app_secret: %s' %app_dict['SECRET'])
        logger.debug('app_id: %s' %app_dict['ID'])
        self.HttpRequest = request
        self._me, self._user_id = None, None
        self.app_dict = app_dict,
        self.app_id, self.app_secret = app_dict['ID'], app_dict['SECRET']
        self.via = 'No token requested'
        self.fb_session = get_session(request)
        if request_token == False:
            return
        if access_token:
            self.via = 'access_token'
        elif request and not force_refresh and self.get_token_from_session():
            self.via = 'session'
        elif request and (not force_refresh and self.get_token_from_cookie()) or \
                          (prefer_cookie and self.get_token_from_cookie()):
            self.via = 'cookie'        
        elif self.get_token_from_app():
            self.via = 'application'
        logger.debug('Got %s token via %s for user id: %s.' % (self.type(), self.via, self._user_id))

    def get_token_from_session(self):
        if not self.fb_session.access_token:
            return None
        self._user_id = self.fb_session.user_id
        if self.type() <> 'user':
            return None
        self.access_token = self.fb_session.access_token
        return self.access_token

    def get_token_from_cookie(self):
        #Client-side authentification writes the signed request into the cookie.
        # Still needs verification from Facebook.
        if not self.HttpRequest.COOKIES.get('fbsr_%i' % int(self.app_id), None):
            return None
        else:
            cookie = self.get_user_from_cookie()

        if cookie and cookie.get('access_token', False):
            self.fb_session.store_token(cookie.get('access_token'))
            self.access_token = cookie.get('access_token')
            self._user_id = cookie.get('uid')
            self.fb_session.user_id = cookie.get('uid')
            return self.access_token
        
        return None        

    def get_token_from_app(self):
        access_token = None
        access_dict = {'type': 'client_cred', 'client_secret': self.app_secret, 'client_id': self.app_id}
        file = urllib.urlopen('https://graph.facebook.com/oauth/access_token?%s'
                              % urllib.urlencode(access_dict))
        raw = file.read()
        try:
            response = _parse_json(raw)
            if response.get("error"):
                raise facebook.GraphAPIError(response["error"]["type"],
                                             response["error"]["message"])
            else:
                raise facebook.GraphAPIError('GET_GRAPH', 'Facebook returned json (%s), expected access_token' % response)
        except:
            # if the response ist not json, it is the access token. Write it back to the session.
            logger.debug('Got Graph Response: %s' % raw)
            if raw.find('=') > -1:
                access_token = raw.split('=')[1]
                self.fb_session.store_token(access_token, None)
            else:
                raise facebook.GraphAPIError('GET_GRAPH', 'Facebook returned bullshit (%s), expected access_token' % response)
        finally:
            file.close()
        if access_token:
            self.access_token = access_token
        return access_token
    
    def get_user_from_cookie(self):
        """ Parses the cookie set by the official Facebook JavaScript SDK. Oauth2 version.
        
        cookies should be a dictionary-like object mapping cookie names to
        cookie values.
    
        If the user is logged in via Facebook, we return a dictionary with the
        keys "uid" and "access_token". The former is the user's Facebook ID,
        and the latter can be used to make authenticated requests to the Graph API.
        If the user is not logged in, we return None.
        
        The cookie contains a signed request containing only the code for authenticating.
        The app has to authenticate with facebook to get the access token.
        """
        sr = self.HttpRequest.COOKIES.get("fbsr_" + self.app_id, "")
        if not sr: return None
        parsed_request = facebook.parseSignedRequest(sr, self.app_secret)
        logger.debug('Parsed request from cookie: %s\n' % parsed_request)
        if 'user_id' in parsed_request:
            self._user_id = int(parsed_request['user_id'])
        if 'code' in parsed_request:
            try:
                response = authenticate(code=parsed_request['code'], 
                              app_id=self.app_id, app_secret=self.app_secret)
            except facebook.GraphAPIError:
                # The code is not valid. Maybe the user has uninstalled the app.
                self.HttpRequest.session.flush()
                self.fb_session.store_token(None)
                return None
            logger.debug('Authenticate returned: %s' % response)
            if 'access_token' in response:
                self.access_token = response['access_token'][0]
            if 'expires' in response:
                token_expires = datetime.now()+timedelta(seconds=int(response['expires'][0]))
            else:
                token_expires = None

        return {'uid': self._user_id, 'access_token': self.access_token, 'token_expires': token_expires }
        

    def _get_me(self, access_token=False):
        if not access_token:
            if not self.access_token or not self.type()=='user' or not self.fb_session.app_is_authenticated:
                return None
            """
            elif self._user_id:
                self._me, created = User.objects.get_or_create(id=self._user_id)
                if created:
                    self._me.get_from_facebook(graph=self, save=True)                
            """
        
        try:
            me = self.request('me')
        except facebook.GraphAPIError as e:
            logger.debug('could not use the accesstoken via %s: %s' % (self.via, e.message))
            self.fb_session.store_token(None)
        else:
            self._user_id = me['id']
            self.fb_session.me = me
            self._me = me  
        #self._me, created = User.objects.get_or_create(id=self._user_id)
        #if created:
        #    self._me.save_from_facebook(me)         
        return self._me

    @property
    def me(self):  # Is now a lazy property.
        if self._me:
            return self._me
        else:
            return self._get_me()

    @property  #DEPRECATED. Kept for compatibility reasons.
    def user(self):
        warnings.warn('The user property is depreceated. Use user_id instead.', DeprecationWarning)
        if self._user_id:
            return self._user_id
        else:
            me = self._get_me(self.access_token)
            return getattr(me, 'id', None)

    @property
    def user_id(self):
        if self._user_id:
            return int(self._user_id)
        else:
            me = self._get_me(self.access_token)
            id = getattr(me, 'id', None)
            return int(id) if id else None
        
    def type(self):
        if not self.access_token:
            return None
        return 'app' if len(self.access_token) < 80 else 'user'

    def revoke_auth(self):
        return self.request('me/permissions', post_args={"method": "delete"})
    
    def put_photo(image, message=None, album_id=None, **kwargs):
        """
        Shortcut for put_media to upload a photo
        """
        self.put_media(image, message, album_id, fxtype='photos', kwargs=kwargs)

    def put_video(image, message=None, album_id=None, **kwargs):
        """
        Shortcut for put_media to upload a video
        """
        self.put_media(image, message, album_id, fxtype='videos', kwargs=kwargs)
    
    def put_media(self, mediafile, message=None, album_id=None, mediatype=None, **kwargs):
        """ Uploads a file using multipart/form-data
            mediafile: File like object for the image
            message: Caption for your image
            album_id: On photos, None posts to /me/photos which uses or creates and uses 
                      an album for your application.
            mediatype: one of 'photos' or 'videos' depending on media type
        """
        object = album_id or "me"
        
        form = MultiPartForm()
        form.add_field('access_token', access_token)
        form.add_field('message', message)
        form.add_file('source', mediafile.name, mediafile)
        if kwargs:
            for k,v in kwargs.items():
                form.add_field(k, v)
    
        request = urllib2.Request('https://graph.facebook.com/%s/%s' % (object, mediatype))
        logger.debug('posting photo to: https://graph.facebook.com/%s/photos %s' % (object, image))
        body = str(form)
        request.add_header('Content-type', form.get_content_type())
        request.add_header('Content-length', len(body))
        request.add_data(body)
    
        raw = urllib2.urlopen(request).read()
        logger.debug('facebook response raw (post image): %s' % raw)
    
        try:
            response = _parse_json(raw)
        except:
            raise facebook.GraphAPIError('GET_GRAPH', 'Facebook returned bullshit (%s), expected json' % response)
    
        """ in some cases, response is not an object """
        if response:
            if response.get("error"):
                raise facebook.GraphAPIError(response["error"]["type"],
                                    response["error"]["message"])
        return response


def get_graph(request=None, app_name=None, app_dict=None, *args, **kwargs):
    """ This is the main factory function that returns a graph class. """
    if not app_dict:
        app_dict = get_app_dict(app_name)
    return Graph(app_dict=app_dict, request=request, *args, **kwargs)

def get_static_graph(app_name=None, app_dict=None, *args, **kwargs):
    """ Explicityl avoid request and user. """
    return get_graph(app_name=app_name, app_dict=app_dict, request=None)

def get_public_graph(app_name=None, app_dict=None, *args, **kwargs):
    """ If you only access public information and don't need an access token. """
    return get_graph(app_name=app_name, app_dict=app_dict, request=None, request_token=False)

def get_session(request=None):
    if not request:
        return FBSessionNoOp()
    else:
        if hasattr(request, 'fb_session'):
            return request.fb_session
        else:
            return FBSession(request) 

def post_image(access_token, image, message, object='me'):
    graph = get_graph()
    graph.access_token = access_token
    return graph.put_media(graph, mediafile=image, message=message, mediatype='photos')


# from http://www.doughellmann.com/PyMOTW/urllib2/
class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              str(value),
            ]
            for name, value in self.form_fields
            )

        # Add the files to upload
        parts.extend(
            [part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              str(body)
            ]
            for field_name, filename, content_type, body in self.files
            )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)


def redirect_GET_session(to, request, permanent=False):
    response = redirect(to, permanent)
    cookie_name = settings.SESSION_COOKIE_NAME

    if cookie_name in request.COOKIES:
        location = response._headers['location'][1]
        separator = '&' if '?' in location else '?'
        response._headers['location'] = ('Location', '%s%s%s=%s' % (location,
                        separator, cookie_name,
                        request.COOKIES.get(cookie_name, '')))
        return response
    else:
        return response
    

def totimestamp(instance):
    """ converts a timeinstance to a timestamp requiered by the Graph API"""
    import time
    return time.mktime(instance.timetuple())
    



