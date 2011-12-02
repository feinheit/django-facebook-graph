from django.conf import settings

def get_app_dict(application=None):
    if not application:
        if getattr(settings, 'FACEBOOK_DEFAULT_APPLICATION', False):
            application = settings.FACEBOOK_APPS[settings.FACEBOOK_DEFAULT_APPLICATION]
        else:
            application = settings.FACEBOOK_APPS.values()[0]
    else:
        application = settings.FACEBOOK_APPS[application]
    return application