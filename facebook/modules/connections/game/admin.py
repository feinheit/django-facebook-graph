from django.contrib import admin

from facebook.modules.base import AdminBase

from .models import Score, Achievement


class ScoreAdmin(AdminBase):
    list_display = ('_user', '_score')
    readonly_fields = ('_user', '_score')
    search_fields = ('_user',)
admin.site.register(Score, ScoreAdmin)


class AchievementAdmin(AdminBase):
    list_display = ('id', '_title', 'points', '_url')
admin.site.register(Achievement, AchievementAdmin)
