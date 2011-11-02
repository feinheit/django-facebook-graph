# -*- coding: utf-8 -*-

import logging
import urllib
logger = logging.getLogger(__name__)
from facebook.graph import GraphAPIError

# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)

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
        raise GraphAPIError(response['error_code'], response['error_msg'])
    return response