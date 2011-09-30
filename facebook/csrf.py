import logging

from django.conf import settings
from django.middleware.csrf import (CsrfViewMiddleware as DjangoCsrfViewMiddleware,
    _sanitize_token, _get_new_csrf_key, _make_legacy_session_token,
    REASON_NO_REFERER, REASON_BAD_REFERER, REASON_NO_COOKIE,
    REASON_NO_CSRF_COOKIE, REASON_BAD_TOKEN, _MAX_CSRF_KEY)
from django.utils.crypto import constant_time_compare
from django.utils.http import same_origin
from django.utils.decorators import decorator_from_middleware

logger = logging.getLogger(__name__)

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

            if not constant_time_compare(request_csrf_token, csrf_token):
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

