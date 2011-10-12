#coding: utf-8
from django.contrib import admin
from models import Score

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    readonly_fields = ('user', 'score')
    search_fields = ('user',)
    ordering = ['score']
    
admin.site.register(Score, ScoreAdmin)