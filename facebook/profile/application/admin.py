#coding: utf-8
from django.contrib import admin
from models import Score

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    readonly_fields = ('user', 'score')
    search_fields = ('user',)
    ordering = ['score']


# TODO: Create a admin model manager that registers models on demand.
admin.site.register(Score, ScoreAdmin)