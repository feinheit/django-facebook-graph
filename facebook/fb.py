""" Use this module for imports. from facebook import fb """

from django.conf import settings

if 'facebook.modules.profile.page' in settings.INSTALLED_APPS:
    from facebook.modules.profile.page.models import Page

if 'facebook.modules.profile.user' in settings.INSTALLED_APPS:
    from facebook.modules.profile.user.models import User, TestUser

if 'facebook.modules.profile.event' in settings.INSTALLED_APPS:
    from facebook.modules.profile.event.models import Event

if 'facebook.modules.profile.application' in settings.INSTALLED_APPS:
    from facebook.modules.profile.application.models import Request

if 'facebook.modules.media' in settings.INSTALLED_APPS:
    from facebook.modules.media.models import Photo

if 'facebook.modules.connections.post' in settings.INSTALLED_APPS:
    from facebook.modules.connections.post.models import Post, PostBase

if 'facebook.modules.connections.game' in settings.INSTALLED_APPS:
    from facebook.modules.connections.game.models import Score, Achievement

