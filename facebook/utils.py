import logging
logger = logging.getLogger(__name__)

import itertools
import mimetools
import mimetypes
import urlparse

import re
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.shortcuts import redirect

from facebook import  get_graph

# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)


def post_image(access_token, image, message, target='me'):
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
