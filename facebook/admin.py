""" Use this module for imports to extend the Admin classes
"""

from django.conf import settings

if 'facebook.modules.profile.page' in settings.INSTALLED_APPS:
    from facebook.modules.profile.page.admin import PageAdmin

if 'facebook.modules.profile.user' in settings.INSTALLED_APPS:
    from facebook.modules.profile.user.admin import UserAdmin

if 'facebook.modules.profile.event' in settings.INSTALLED_APPS:
    from facebook.modules.profile.event.admin import EventAdmin

if 'facebook.modules.profile.application' in settings.INSTALLED_APPS:
    from facebook.modules.profile.application.admin import RequestAdmin

if 'facebook.modules.media' in settings.INSTALLED_APPS:
    from facebook.modules.media.admin import PhotoAdmin

if 'facebook.modules.connections.post' in settings.INSTALLED_APPS:
    from facebook.modules.connections.post.admin import PostAdmin

if 'facebook.modules.connections.game' in settings.INSTALLED_APPS:
    from facebook.modules.connections.game.admin import ScoreAdmin, AchievementAdmin


