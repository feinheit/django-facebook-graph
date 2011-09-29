# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from models import Score, Like
from utils import get_graph

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    readonly_fields = ('user', 'score')
    search_fields = ('user',)
    ordering = ['score']
    
admin.site.register(Score, ScoreAdmin)

class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', '_name', '_category')
    search_fields = ('user', '_name')
    ordering = ['user', '_created_time']
    
admin.site.register(Like, LikeAdmin)
