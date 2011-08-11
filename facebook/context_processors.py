from django.conf import settings
""" This context processor is depreciated.
    It only works it if you only have one Facebook App. 
    Use the fb_tags instead.
"""
def application_settings(request):
    firstapp = getattr(settings, 'FACEBOOK_APPS').values()[0]
    return { 'FACEBOOK_API_KEY' : firstapp['API-KEY'],
             'FACEBOOK_APP_ID' : firstapp['ID'],
             'FACEBOOK_CANVAS_PAGE' : firstapp['CANVAS-PAGE'],
             'FACEBOOK_CANVAS_URL' : firstapp['CANVAS-URL']}
    
def facebook_config(request):
    return {'facebook' : request.session['facebook']}

def session_without_cookies(request):
    """ simple helper to use sessions without cookies """
    cookie_name = settings.SESSION_COOKIE_NAME
    session_key = request.session._get_session_key()
    
    return {'session_GET' : '%s=%s' %(cookie_name, session_key),
            'session_id'  : session_key,
            'session_hidden_field' : '<div style="display:none"><input type="hidden" name="%s" value="%s" /></div>' %(cookie_name, session_key)}

def is_page_fan(request):
    """ checks if the user likes the page, the tab is in. """
    try:    
        is_fan = request.fb_session.signed_request['page']['liked']
    except (AttributeError, KeyError, TypeError):
        is_fan = False
    return {'is_fan' : is_fan, 'signed_request': request.fb_session.signed_request }