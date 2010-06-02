from django.conf import settings

def facebook_keys(request):
    return { 'FACEBOOK_API_KEY' : settings.FACEBOOK_API_KEY,
             'FACEBOOK_APP_SECRET' : settings.FACEBOOK_APP_SECRET, 
             'FACEBOOK_APP_ID' : settings.FACEBOOK_APP_ID }