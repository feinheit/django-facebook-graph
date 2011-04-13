from django.conf import settings

def application_settings(request):
    return { 'FACEBOOK_API_KEY' : getattr(settings, 'FACEBOOK_API_KEY', ''),
             'FACEBOOK_APP_ID' : getattr(settings, 'FACEBOOK_APP_ID', ''),
             'FACEBOOK_CANVAS_PAGE' : getattr(settings, 'FACEBOOK_CANVAS_PAGE', ''),
             'FACEBOOK_CANVAS_URL' : getattr(settings, 'FACEBOOK_CANVAS_URL', ''),}
    
def facebook_config(request):
    return {'facebook' : request.session['facebook']}

def session_without_cookies(request):
    """ simple helper to use sessions without cookies """
    cookie_name = settings.SESSION_COOKIE_NAME
    session_key = request.session._get_session_key()
    
    return {'session_GET' : '%s=%s' %(cookie_name, session_key),
            'session_id'  : session_key,
            'session_hidden_field' : '<div style="display:none"><input type="hidden" name="%s" value="%s" /></div>' %(cookie_name, session_key)}
