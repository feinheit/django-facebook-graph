#coding=utf-8

import functools, logging, sys
from facebook.modules.profile.application.utils import get_app_dict
from django.core.urlresolvers import resolve, Resolver404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.defaultfilters import urlencode
logger = logging.getLogger(__name__)

runserver = ('runserver' in sys.argv)


def redirect_to_page(app_name=None):
    def _redirect_to_page(view):
        """ Decorator that redirects a canvas URL to a page using the path that is in app_data.path """
        """ Decorate the views where you have links to the app page. """
    
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            request = args[0]
            # if this is already the callback, do not wrap.
            if getattr(request, 'avoid_redirect', False):
                logger.debug('entered calback. View: %s, kwargs: %s' %(view, kwargs))
                return view(*args, **kwargs)
    
            session = request.session.get('facebook', dict())
            try:
                signed_request = session['signed_request']
            except KeyError:
                logger.debug('No signed_request in current session. Returning View.')
                return view(*args, **kwargs)
            
            app_dict = get_app_dict(app_name)
    
            logger.debug('signed_request: %s' %signed_request)
            if 'app_data' in signed_request:
                app_data = signed_request['app_data']
                del request.session['facebook']['signed_request']['app_data']
                request.session.modified = True
                logger.debug('found app_data url: %s' %app_data)
                #return HttpResponseRedirect(app_data)
                try:
                    original_view = resolve(app_data)
                except Resolver404:
                    logger.debug('Did not find view for %s.' %app_data)
                    url = u'%s?sk=app_%s' % (app_dict['REDIRECT_URL'], app_dict['ID'])
                    return render_to_response('redirecter.html', {'destination': url }, RequestContext(request))
    
                logger.debug('found original view url: %s' %original_view)
                setattr(request, 'avoid_redirect' ,  True)
                # call the view that was originally requested:
                return original_view.func(request, *original_view.args, **original_view.kwargs)
            else:
                #check if the app is inside the specified page.
                try:
                    page = signed_request['page']['id']
                except KeyError:
                    page = None

                if page <> app_dict['PAGE_ID'] and not runserver:
                    logger.debug('Tab is not in original Page. Redirecting...')
                    url = u'%s?sk=app_%s&app_data=%s' % (app_dict['REDIRECT_URL'], app_dict['ID'], urlencode(request.path))
                    return render_to_response('redirecter.html', {'destination': url }, RequestContext(request))

            return view(*args, **kwargs)
    
        return wrapper
    return _redirect_to_page