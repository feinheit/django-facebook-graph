#!/usr/bin/env python

"""Python client library for the Facebook Platform.

This client library is designed to support the Graph API and the official
Facebook JavaScript SDK, which is the canonical way to implement
Facebook authentication. Read more about the Graph API at
http://developers.facebook.com/docs/api. You can download the Facebook
JavaScript SDK at http://github.com/facebook/connect-js/.

This library is adapted to work with the current SDK and Graph API.

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

from graph import GraphAPIError, get_graph, get_static_graph, get_public_graph
from session import get_session
from modules.profile.application.utils import get_app_dict
from fql import get_FQL

