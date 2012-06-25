import logging

from django.conf import settings
import django
import re

from django.utils import crypto
from django.utils.http import same_origin
from django.utils.decorators import decorator_from_middleware
from django.middleware.csrf import CsrfViewMiddleware as DjangoCsrfViewMiddleware, \
    REASON_NO_REFERER, REASON_BAD_REFERER, REASON_NO_CSRF_COOKIE, REASON_BAD_TOKEN

logger = logging.getLogger(__name__)

CSRF_KEY_LENGTH = 32

import warnings
warnings.warn('facebook.csrf.CsrfViewMiddleware is no longer necessary. '
              'Just make sure the SignedRequestMiddleware gets called before the '
              'standard django CsrfViewMiddleware.', DeprecationWarning, stacklevel=2)

# CSRF view middleware changed significantly in Django 1.4

if django.VERSION[0]==1 and django.VERSION[1] >= 4:

    from django.middleware.csrf import _get_failure_view

    def _get_new_csrf_key():
        return crypto.get_random_string(CSRF_KEY_LENGTH)

    def _sanitize_token(token):
        # Allow only alphanum, and ensure we return a 'str' for the sake
        # of the post processing middleware.
        if len(token) > CSRF_KEY_LENGTH:
            return _get_new_csrf_key()
        token = re.sub('[^a-zA-Z0-9]+', '', str(token.decode('ascii', 'ignore')))
        if token == "":
            # In case the cookie has been truncated to nothing at some point.
            return _get_new_csrf_key()
        return token

    class CsrfViewMiddleware(DjangoCsrfViewMiddleware):
        """
        Patched Middleware that accepts POSTs from Facebook
        """
        # The _accept and _reject methods currently only exist for the sake of the
        # requires_csrf_token decorator.
        def _accept(self, request):
            request.csrf_processing_done = True
            return None

        def _reject(self, request, reason):
            return _get_failure_view()(request, reason=reason)

        def process_view(self, request, callback, callback_args, callback_kwargs):

            if getattr(request, 'csrf_processing_done', False):
                return None

            try:
                csrf_token = _sanitize_token(
                    request.COOKIES[settings.CSRF_COOKIE_NAME])
                # Use same token next time
                request.META['CSRF_COOKIE'] = csrf_token
            except KeyError:
                if 'state' in request.POST:
                    csrf_token = _sanitize_token(request.POST.get('state'))
                else:
                    csrf_token = None
                    # Generate token and store it in the request, so it's
                    # available to the view.
                    request.META["CSRF_COOKIE"] = _get_new_csrf_key()

            # Wait until request.META["CSRF_COOKIE"] has been manipulated before
            # bailing out, so that get_token still works
            if getattr(callback, 'csrf_exempt', False):
                return None

            # Assume that anything not defined as 'safe' by RC2616 needs protection
            if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
                if getattr(request, '_dont_enforce_csrf_checks', False):
                    # Mechanism to turn off CSRF checks for test suite.
                    # It comes after the creation of CSRF cookies, so that
                    # everything else continues to work exactly the same
                    # (e.g. cookies are sent, etc.), but before any
                    # branches that call reject().
                    return self._accept(request)

                # let initial signed requests pass
                if request.method == 'POST' and 'signed_request' in request.POST:
                    post = request.POST.copy()
                    post.pop('signed_request')
                    if len(post) == 0:
                        return self._accept(request)

                if request.is_secure() and getattr(settings, 'HTTPS_REFERER_REQUIRED', True):
                    # Suppose user visits http://example.com/
                    # An active network attacker (man-in-the-middle, MITM) sends a

                    referer = request.META.get('HTTP_REFERER')
                    if referer is None:
                        logger.warning('Forbidden (%s): %s',
                                       REASON_NO_REFERER, request.path,
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, REASON_NO_REFERER)

                    # Note that request.get_host() includes the port.
                    good_referer = 'https://%s/' % request.get_host()
                    if not same_origin(referer, good_referer):
                        reason = REASON_BAD_REFERER % (referer, good_referer)
                        logger.warning('Forbidden (%s): %s', reason, request.path,
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, reason)

                if csrf_token is None:
                    # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
                    # and in this way we can avoid all CSRF attacks, including login
                    # CSRF.
                    logger.warning('Forbidden (%s): %s',
                                   REASON_NO_CSRF_COOKIE, request.path,
                        extra={
                            'status_code': 403,
                            'request': request,
                        }
                    )
                    return self._reject(request, REASON_NO_CSRF_COOKIE)

                # Check non-cookie token for match.
                request_csrf_token = ""
                if request.method == "POST":
                    request_csrf_token = request.POST.get('csrfmiddlewaretoken', '')

                if request_csrf_token == "":
                    # Fall back to X-CSRFToken, to make things easier for AJAX,
                    # and possible for PUT/DELETE.
                    request_csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')

                if not crypto.constant_time_compare(request_csrf_token, csrf_token):
                    logger.warning('Forbidden (%s): %s',
                                   REASON_BAD_TOKEN, request.path,
                        extra={
                            'status_code': 403,
                            'request': request,
                        }
                    )
                    return self._reject(request, REASON_BAD_TOKEN)

            return self._accept(request)



else:
    from django.middleware.csrf import (
        _sanitize_token, _get_new_csrf_key, _make_legacy_session_token,
        REASON_NO_COOKIE, _MAX_CSRF_KEY)

    class CsrfViewMiddleware(DjangoCsrfViewMiddleware):

        def process_view(self, request, callback, callback_args, callback_kwargs):
            if getattr(request, 'csrf_processing_done', False):
                return None

            try:
                request.META["CSRF_COOKIE"] = _sanitize_token(request.COOKIES[settings.CSRF_COOKIE_NAME])
                cookie_is_new = False
            except KeyError:
                request.META["CSRF_COOKIE"] = _get_new_csrf_key()
                cookie_is_new = True

            if getattr(callback, 'csrf_exempt', False):
                return None

            if request.method == 'POST':
                if getattr(request, '_dont_enforce_csrf_checks', False):
                    return self._accept(request)
                # let initial signed requests pass
                if 'signed_request' in request.POST:
                    post = request.POST.copy()
                    post.pop('signed_request')
                    if len(post) == 0:
                        return self._accept(request)

                if request.is_secure() and getattr(settings, 'HTTPS_REFERER_REQUIRED', True):
                    referer = request.META.get('HTTP_REFERER')
                    if referer is None :
                        logger.warning('Forbidden (%s): %s' % (REASON_NO_REFERER, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, REASON_NO_REFERER)

                    # Note that request.get_host() includes the port
                    good_referer = 'https://%s/' % request.get_host()
                    if not same_origin(referer, good_referer):
                        reason = REASON_BAD_REFERER % (referer, good_referer)
                        logger.warning('Forbidden (%s): %s' % (reason, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, reason)

                if cookie_is_new:
                    try:
                        session_id = request.COOKIES[settings.SESSION_COOKIE_NAME]
                        csrf_token = _make_legacy_session_token(session_id)
                    except KeyError:
                        logger.warning('Forbidden (%s): %s' % (REASON_NO_COOKIE, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, REASON_NO_COOKIE)
                else:
                    csrf_token = request.META["CSRF_COOKIE"]

                # check incoming token
                request_csrf_token = request.POST.get('csrfmiddlewaretoken', None)
                if not request_csrf_token:
                    request_csrf_token = request.POST.get('state', '')
                if request_csrf_token == "":
                    # Fall back to X-CSRFToken, to make things easier for AJAX
                    request_csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')

                if not crypto.constant_time_compare(request_csrf_token, csrf_token):
                    if cookie_is_new:
                        # probably a problem setting the CSRF cookie
                        logger.warning('Forbidden (%s): %s' % (REASON_NO_CSRF_COOKIE, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, REASON_NO_CSRF_COOKIE)
                    else:
                        logger.warning('Forbidden (%s): %s' % (REASON_BAD_TOKEN, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, REASON_BAD_TOKEN)

            return self._accept(request)


csrf_protect = decorator_from_middleware(CsrfViewMiddleware)
csrf_protect.__name__ = "csrf_protect"
csrf_protect.__doc__ = """
This decorator adds CSRF protection in exactly the same way as
CsrfViewMiddleware, but it can be used on a per view basis.  Using both, or
using the decorator multiple times, is harmless and efficient.
"""

