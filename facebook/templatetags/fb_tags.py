#coding=utf-8
from django import template
from django.conf import settings
from facebook.utils import get_app_dict
register = template.Library()
from django.utils.safestring import mark_safe

@register.simple_tag
def fb_app_settings(app_id=None):
    """ Returns a link to the user's app settings page for the current app. """
    if not settings.DEBUG:
        return ''
    else:
        if not app_id:
            app = get_app_dict()
            app_id = app['ID']
        link = '<a id="fb_app_settings_link" href="http://www.facebook.com/settings/?tab=applications&app_id=%s" target="_blank">X</a>' % app_id
        return mark_safe(link)
    
@register.simple_tag
def fb_api_key(app_name=None):
    app = get_app_dict(app_name)
    return app['API-KEY']

@register.simple_tag
def fb_app_id(app_name=None):
    app = get_app_dict(app_name)
    return app['ID']

@register.simple_tag
def fb_canvas_page(app_name=None):
    app = get_app_dict(app_name)
    return app['CANVAS-PAGE']

@register.simple_tag
def fb_canvas_url(request, app_name=None):
    app = get_app_dict(app_name)
    if request.is_secure:
        return app['SECURE-CANVAS-URL']
    else:
        return app['CANVAS-URL']

@register.simple_tag
def fb_redirect_url(app_name=None):
    app = get_app_dict(app_name)
    return app['REDIRECT-URL']