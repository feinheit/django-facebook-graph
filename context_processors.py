from django.conf import settings

def facebook_keys(request):
    return { 'FACEBOOK_API_KEY' : getattr(settings, 'FACEBOOK_API_KEY', ''),
             'FACEBOOK_APP_SECRET' : getattr(settings, 'FACEBOOK_APP_SECRET', ''), 
             'FACEBOOK_APP_ID' : getattr(settings, 'FACEBOOK_APP_ID', '') }