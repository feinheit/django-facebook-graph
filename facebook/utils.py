import logging

logger = logging.getLogger(__name__)

import urlparse

import re
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.shortcuts import redirect


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
    return time.mktime(instance.timetuple())
    

def validate_redirect(url):
    """ validates the redirect url """
    
    valid = re.compile(r'^[a-zA-Z0-9_?=&.:/-]+$')
    
    if not valid.match(url):
        return False
        
    domain = urlparse.urlparse(url).netloc
    if domain.find('www.') == 0:
        domain = domain[4:]
    if Site.objects.filter(domain=domain):
        return True
    else:
        for APP in getattr(settings, 'FACEBOOK_APPS', []):
            parsed_canvas = urlparse.urlparse(settings.FACEBOOK_APPS[APP]['CANVAS-PAGE'])
            if 0 < url.find(parsed_canvas.netloc + parsed_canvas.path ) <= 8:
                logger.info(parsed_canvas)
                return True
    return False



