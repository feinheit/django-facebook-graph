from django.contrib import admin

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')
    readonly_fields = ('user', 'score')
    search_fields = ('user',)
    ordering = ['score']