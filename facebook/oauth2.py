# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

import hmac
import hashlib
import urllib
import base64
import urlparse

import facebook

# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)


def base64_url_decode(s):
    return base64.urlsafe_b64decode(s.encode("utf-8") + '=' * (4 - len(s) % 4))


def parseSignedRequest(signed_request, secret=None, application=None):
    """
    adapted from from
    http://web-phpproxy.appspot.com/687474703A2F2F7061737469652E6F72672F31303536363332
    https://github.com/facebook/python-sdk/commit/cb43c5a4a4b8c3e66264ed5508871b175f9c515f
    """

    if not secret:
        from facebook.modules.profile.application import get_app_dict
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
            raise facebook.graph.GraphAPIError('AUTHENTICATION ERROR', 'Facebook returned this: %s. Expected access token.' % raw)
        else:
            if isinstance(response, dict) and response.get("error"):
                # The Code is invalid. Maybe the user logged out of Facebook or removed the app.
                raise facebook.graph.GraphAPIError(response["error"]["type"],
                                             response["error"]["message"])
            else:
                raise facebook.graph.GraphAPIError('AUTHENTICATION ERROR', 'Facebook returned json (%s), expected access_token' % response)
        
    logger.debug('Authentication Graph Response: %s' % response)
    return response