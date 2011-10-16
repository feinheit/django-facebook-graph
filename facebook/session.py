# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from facebook.profile.application.models import Request
import logging
logger = logging.getLogger(__name__)


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
        elif isinstance(item, Request):
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
    

def get_session(request=None):
    if not request:
        return FBSessionNoOp()
    else:
        if hasattr(request, 'fb_session'):
            return request.fb_session
        else:
            return FBSession(request) 
