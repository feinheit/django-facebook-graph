from django.conf import settings

def application_settings(request):
    return { 'FACEBOOK_API_KEY' : getattr(settings, 'FACEBOOK_API_KEY', ''),
             'FACEBOOK_APP_ID' : getattr(settings, 'FACEBOOK_APP_ID', ''),
             'FACEBOOK_CANVAS_PAGE' : getattr(settings, 'FACEBOOK_CANVAS_PAGE', ''),
             'FACEBOOK_CANVAS_URL' : getattr(settings, 'FACEBOOK_CANVAS_URL', ''),}
    
def facebook_config(request):
    return {'facebook' : request.session['facebook']}