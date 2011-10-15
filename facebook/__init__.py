#!/usr/bin/env python

"""Python client library for the Facebook Platform.

This client library is designed to support the Graph API and the official
Facebook JavaScript SDK, which is the canonical way to implement
Facebook authentication. Read more about the Graph API at
http://developers.facebook.com/docs/api. You can download the Facebook
JavaScript SDK at http://github.com/facebook/connect-js/.

This library is adapted to work with the current SDK and Graph API.

"""

import base64
from django.conf import settings
import urllib
import logging
import hmac
import hashlib
logger = logging.getLogger(__name__)
import urlparse


from graph import GraphAPIError, get_graph, get_static_graph, get_public_graph
from session import get_session
from fql import get_FQL
from profile.user.models import User as FbUser
from profile.page.models import Page as FbPage
from profile.event.models import Event as FbEvent


# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)


"""
Example App Settings Entry:

FACEBOOK_APPS = {
    'My great App' : {
            'ID': '155XXXXXXXXXXX',
            'SECRET': 'cbXXXXXXXXXXXXXXXXXXXXXd8',
            'CANVAS-PAGE': 'http://apps.facebook.com/mygreatapp/',
            'CANVAS-URL': 'http://localhost.local/',
            'SECURE-CANVAS-URL': 'https://localhost.local/',
            'REDIRECT-URL': 'http://apps.facebook.com/mygreatapp/',
            'DOMAIN': 'localhost.local:8000',
    }
}

"""

def get_app_dict(application=None):
    if not application:
        if getattr(settings, 'FACEBOOK_DEFAULT_APPLICATION', False):
            application = settings.FACEBOOK_APPS[settings.FACEBOOK_DEFAULT_APPLICATION]
        else:
            application = settings.FACEBOOK_APPS.values()[0]
    else:
        application = settings.FACEBOOK_APPS[application]
    return application


def base64_url_decode(s):
    return base64.urlsafe_b64decode(s.encode("utf-8") + '=' * (4 - len(s) % 4))


def parseSignedRequest(signed_request, secret=None, application=None):
    """
    adapted from from
    http://web-phpproxy.appspot.com/687474703A2F2F7061737469652E6F72672F31303536363332
    https://github.com/facebook/python-sdk/commit/cb43c5a4a4b8c3e66264ed5508871b175f9c515f
    """

    if not secret:
        app_dict = get_app_dict(application)
        secret = app_dict['SECRET']
    
    try:
        (encoded_sig, payload) = signed_request.split(".", 2)
    except IndexError:
        raise ValueError("Signed Request is malformed")
    
    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))

    if data.get("algorithm").upper() != "HMAC-SHA256":
        raise ValueError("'signed_request' is using an unknown algorithm")
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        raise ValueError("'signed_request' signature mismatch")
    
    return data


def authenticate(app_id, app_secret, code=None, redirect_uri="", type=None):
    
    args = {'client_id': app_id,
            'client_secret': app_secret,
            'redirect_uri': redirect_uri
            }
    if code:  args['code'] =  code.replace("\"", "")
    if type:  args['type'] = 'client_cred'
    
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
            raise GraphAPIError('AUTHENTICATION ERROR', 'Facebook returned this: %s. Expected access token.' % raw)
        else:
            if isinstance(response, dict) and response.get("error"):
                # The Code is invalid. Maybe the user logged out of Facebook or removed the app.
                raise GraphAPIError(response["error"]["type"],
                                             response["error"]["message"])
            else:
                raise GraphAPIError('AUTHENTICATION ERROR', 'Facebook returned json (%s), expected access_token' % response)
        
    logger.debug('Authentication Graph Response: %s' % response)
    return response

