import logging
import sys

logger = logging.getLogger(__name__)

import urlparse

import re
import time

import urllib
import urllib2
import mimetools, mimetypes
import os, stat
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import warnings

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


def warn_gone(item):
    warnings.warn('%s has been removed by Facebook' %item, DeprecationWarning, stacklevel=2)

def warn_deprecated(item):
    warnings.warn('%s has been deprecated by Facebook and will be removed soon.' %item,
        DeprecationWarning, stacklevel=2)



# 02/2006 Will Holcomb <wholcomb@gmail.com>
# 7/26/07 Slightly modified by Brian Schneider  
# in order to support unicode files ( multipart_encode function )

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

# Controls how sequences are uncoded. If true, elements may be given multiple values by
#  assigning a sequence.
doseq = 1

class MultipartPostHandler(urllib2.BaseHandler):
    handler_order = urllib2.HTTPHandler.handler_order - 10 # needs to run first

    def http_request(self, request):
        data = request.get_data()
        if data is not None and type(data) != str:
            v_files = []
            v_vars = []
            try:
                for(key, value) in data.items():
                    if type(value) == file:
                        v_files.append((key, value))
                    else:
                        v_vars.append((key, value))
            except TypeError:
                systype, value, traceback = sys.exc_info()
                raise TypeError, "not a valid non-string sequence or mapping object", traceback

            if len(v_files) == 0:
                data = urllib.urlencode(v_vars, doseq)
            else:
                boundary, data = self.multipart_encode(v_vars, v_files)

                contenttype = 'multipart/form-data; boundary=%s' % boundary
                #if(request.has_header('Content-Type')
                #   and request.get_header('Content-Type').find('multipart/form-data') != 0):
                #    print "Replacing %s with %s" % (request.get_header('content-type'), 'multipart/form-data')
                request.add_unredirected_header('Content-Type', contenttype)

            request.add_data(data)
        
        return request

    def multipart_encode(vars, files, boundary = None, buf = None):
        if boundary is None:
            boundary = mimetools.choose_boundary()
        if buf is None:
            buf = StringIO()
        for(key, value) in vars:
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"' % key)
            buf.write('\r\n\r\n' + value + '\r\n')
        for(key, fd) in files:
            file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
            filename = fd.name.split('/')[-1]
            contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
            buf.write('Content-Type: %s\r\n' % contenttype)
            # buffer += 'Content-Length: %s\r\n' % file_size
            fd.seek(0)
            buf.write('\r\n' + fd.read() + '\r\n')
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf
    multipart_encode = Callable(multipart_encode)

    https_request = http_request

def do_exchange_token(app_dict, exchange_token):
    """ Exchanges the access token for a 60 day token.
    """
    args = {'client_id' : app_dict['ID'],
                'client_secret': app_dict['SECRET'],
                'grant_type': 'fb_exchange_token',
                'fb_exchange_token': exchange_token
                }
    file = urllib.urlopen("https://graph.facebook.com/oauth/access_token",
            urllib.urlencode(args))
    raw = file.read()
    file.close()
    response = urlparse.parse_qs(raw)
    # values are returned as lists.
    response = dict((k, v[0]) for k,v in response.items())
    return response