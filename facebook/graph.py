# -*- coding: utf-8 -*-

import urllib
import urllib2
import warnings
from urllib2 import HTTPError

from facebook.utils import MultipartPostHandler

import logging
from django.http import HttpResponseServerError
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta

from facebook.modules.profile.application.utils import get_app_dict
from facebook.oauth2 import authenticate, parseSignedRequest
from facebook.session import get_session

# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)


class GraphAPIError(Exception):
    def __init__(self, type, message):
        Exception.__init__(self)
        self.type = type
        self.message = message
    
    def __str__(self):
        return '%s: %s' % (self.type, self.message)


class GraphAPI(object):
    """A client for the Facebook Graph API.

    See http://developers.facebook.com/docs/api for complete documentation
    for the API.

    The Graph API is made up of the objects in Facebook (e.g., people, pages,
    events, photos) and the connections between them (e.g., friends,
    photo tags, and event RSVPs). This client provides access to those
    primitive types in a generic way. For example, given an OAuth access
    token, this will fetch the profile of the active user and the list
    of the user's friends:

       graph = facebook.GraphAPI(access_token)
       user = graph.get_object("me")
       friends = graph.get_connections(user["id"], "friends")

    You can see a list of all of the objects and connections supported
    by the API at http://developers.facebook.com/docs/reference/api/.

    You can obtain an access token via OAuth or by using the Facebook
    JavaScript SDK. See http://developers.facebook.com/docs/authentication/
    for details.

    If you are using the JavaScript SDK, you can use the
    get_user_from_cookie() method below to get the OAuth access token
    for the active user from the cookie saved by the SDK.
    """
    def __init__(self, access_token=None):
        self.access_token = access_token

    def get_object(self, id, **args):
        """Fetchs the given object from the graph."""
        return self.request(id, args)

    def get_objects(self, ids, **args):
        """Fetchs all of the given object from the graph.

        We return a map from ID to object. If any of the IDs are invalid,
        we raise an exception.
        """
        args["ids"] = ",".join(ids)
        return self.request("", args)

    def get_connections(self, id, connection_name, **args):
        """Fetchs the connections for given object."""
        return self.request(id + "/" + connection_name, args)

    def put_object(self, parent_object, connection_name, **data):
        """Writes the given object to the graph, connected to the given parent.

        For example,

            graph.put_object("me", "feed", message="Hello, world")

        writes "Hello, world" to the active user's wall. Likewise, this
        will comment on a the first post of the active user's feed:

            feed = graph.get_connections("me", "feed")
            post = feed["data"][0]
            graph.put_object(post["id"], "comments", message="First!")

        See http://developers.facebook.com/docs/api#publishing for all of
        the supported writeable objects.

        Most write operations require extended permissions. For example,
        publishing wall posts requires the "publish_stream" permission. See
        http://developers.facebook.com/docs/authentication/ for details about
        extended permissions.
        """
        assert self.access_token, "Write operations require an access token"
        return self.request(parent_object + "/" + connection_name, post_args=data)

    def put_wall_post(self, message, attachment={}, profile_id="me"):
        """Writes a wall post to the given profile's wall.

        We default to writing to the authenticated user's wall if no
        profile_id is specified.

        attachment adds a structured attachment to the status message being
        posted to the Wall. It should be a dictionary of the form:

            {"name": "Link name"
             "link": "http://www.example.com/",
             "caption": "{*actor*} posted a new review",
             "description": "This is a longer description of the attachment",
             "picture": "http://www.example.com/thumbnail.jpg"}

        """
        return self.put_object(profile_id, "feed", message=message, **attachment)

    def put_comment(self, object_id, message):
        """Writes the given comment on the given post."""
        return self.put_object(object_id, "comments", message=message)

    def put_like(self, object_id):
        """Likes the given post."""
        return self.put_object(object_id, "likes")

    def delete_object(self, id):
        """Deletes the object with the given ID from the graph."""
        return self.request(id, post_args={"method": "delete"})

    def request(self, path, args=None, post_args=None):
        """Fetches the given path in the Graph API.

        We translate args to a valid query string. If post_args is given,
        we send a POST request to the given path with the given arguments.
        """
        if not args: args = {}
        if self.access_token:
            if post_args is not None:
                post_args["access_token"] = self.access_token
            else:
                args["access_token"] = self.access_token
        if post_args:
            for k, v in post_args.iteritems():
                if isinstance(v, basestring):
                    post_args[k] = v.encode('utf-8')
        post_data = None if post_args is None else urllib.urlencode(post_args)
        query = "https://graph.facebook.com/" + path + "?" + urllib.urlencode(args)
        logger.debug('query: %s' % query)
        try:
            file = urllib2.urlopen(query, post_data)
            raw = file.read()
        except HTTPError as e:  # attrs: filename, code, msg, hdrs, fp
            if e.fp is not None:
                r = _parse_json(e.fp.read())
                raise GraphAPIError(r['error']['type'], r['error']['message'])
            else:
                raise GraphAPIError('HTTP ERROR %s' % e.code, '%s, %s %s' % (e.msg, e.filename, e.fp.read()))
        logger.debug('facebook response raw: %s, query: %s' % (raw, query))
        try:
            response = _parse_json(raw)
            if isinstance(response, dict) and response.get("error"):
                raise GraphAPIError(response["error"]["type"],
                                    response["error"]["message"])
        except AttributeError:
            pass
        finally:
            file.close()
            
        return response
    

class Graph(GraphAPI):
    """ The Base Class for a Facebook Graph. Inherits from the Facebook SDK Class.
    Tries to get a facebook graph using different methods.
    * via access_token: that one is simple
    * via request cookie (access token)
    * via application -> create an accesstoken for an application if requested.
    Needs OAuth2ForCanvasMiddleware to deal with the signed Request and Authentication code.
    Put any graph.get_... calls in a try except structure. An Access Token might be invalid.
    In that case a GraphAPIError is raised.
    
    """
    def __init__(self, app_dict, request=None, access_token=None, 
                 request_token=True, force_refresh=False,
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
        elif request and (self.get_token_from_cookie()) or \
                          (prefer_cookie and self.get_token_from_cookie()):
            self.via = 'cookie'        
        elif self.get_token_from_app():
            self.via = 'application'
        logger.debug('Got %s token via %s for user id: %s.' % (self.type(), self.via, self._user_id))

    def get_token_from_session(self):
        if not self.fb_session.access_token:
            return None
        self._user_id = self.fb_session.user_id
        if self.type(token=self.fb_session.access_token) <> 'user':
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
        try:
            response = authenticate(app_id=self.app_id, app_secret=self.app_secret, type='client_cred')
        except GraphAPIError:
        # The code is not valid. Maybe the user has uninstalled the app.
            self.HttpRequest.session.flush()
            self.fb_session.store_token(None)
            return None
        
        if 'access_token' in response:
            self.access_token = response['access_token'][0]
        if 'expires' in response:
            token_expires = datetime.now()+timedelta(seconds=int(response['expires'][0]))
        else:
            token_expires = None
            self.fb_session.store_token(self.access_token, token_expires)
        return self.access_token
    
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
        parsed_request = parseSignedRequest(sr, self.app_secret)
        logger.debug('Parsed request from cookie: %s\n' % parsed_request)
        if 'user_id' in parsed_request:
            self._user_id = int(parsed_request['user_id'])
        if 'code' in parsed_request:
            try:
                response = authenticate(code=parsed_request['code'], 
                              app_id=self.app_id, app_secret=self.app_secret)
            except GraphAPIError:
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
        
        try:
            me = self.request('me')
        except GraphAPIError as e:
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
            return me.get('id', None)

    @property
    def user_id(self):
        if self._user_id:
            return int(self._user_id)
        else:
            me = self._get_me(self.access_token)
            id = me.get('id', None)
            return int(id) if id else None
        
    def type(self, token=None):
        access_token = token or self.access_token
        if not access_token:
            return None
        return 'app' if len(access_token) < 80 else 'user'

    def revoke_auth(self):
        return self.request('me/permissions', post_args={"method": "delete"})
    
    def put_photo(self, image, message='', album_id=None, **kwargs):
        """
        Shortcut for put_media to upload a photo
        """
        return self.put_media(image, message, album_id, mediatype='photos', kwargs=kwargs)

    def put_video(self, image, message='', album_id=None, **kwargs):
        """
        Shortcut for put_media to upload a video
        """
        return self.put_media(image, message, album_id, mediatype='videos', kwargs=kwargs)
    
    def put_media(self, mediafile, message='', album_id=None, mediatype=None, **kwargs):
        """ Uploads a file using multipart/form-data
            mediafile: File like object for the image
            message: Caption for your image
            album_id: On photos, None posts to /me/photos which uses or creates and uses 
                      an album for your application.
            mediatype: one of 'photos' or 'videos' depending on media type
        """
        object = album_id or "me"
        
        opener = urllib2.build_opener(MultipartPostHandler)
        try:
            source = open(mediafile.name, 'rb')
            source.seek(0)
            params = {'source' : source, 'message': message }
            upload = opener.open('https://graph.facebook.com/%s/%s?access_token=%s' % 
                              (object, mediatype, self.access_token), params)
            raw = upload.fp.read()
            upload.close()
        except IOError as e:
            return HttpResponseServerError(e)
        finally:
            source.close()

        logger.debug('facebook response raw (post image): %s' % raw)
    
        try:
            response = _parse_json(raw)
        except:
            raise GraphAPIError('GET_GRAPH', 'Facebook returned bullshit (%s), expected json' % response)
    
        """ in some cases, response is not an object """
        if response:
            if response.get("error"):
                raise GraphAPIError(response["error"]["type"],
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


    
