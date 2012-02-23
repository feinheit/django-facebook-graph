"""
    Dummy model to get old references to the new structured models.
    Needed by south

    possible rewrite with dynamic imports http://www.diveintopython.net/functional_programming/dynamic_import.html
"""

from django.conf import settings

if 'facebook.modules.profile.page' in settings.INSTALLED_APPS:
    from facebook.modules.profile.page.models import Page

if 'facebook.modules.profile.user' in settings.INSTALLED_APPS:
    from facebook.modules.profile.user.models import User, TestUser

if 'facebook.modules.profile.event' in settings.INSTALLED_APPS:
    from facebook.modules.profile.event.models import Event

if 'facebook.modules.profile.application' in settings.INSTALLED_APPS:
    from facebook.modules.profile.application.models import Request