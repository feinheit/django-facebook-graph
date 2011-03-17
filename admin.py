from django.contrib import admin

from models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile_link', 'access_token', 'user', '_name', 'created', 'updated',)
    readonly_fields = ('friends', '_name', '_first_name', '_last_name', '_link', '_birthday', '_email', '_location', '_gender', '_graph')
    search_fields = ('id', '_name')
    
    def profile_link(self, obj):
        if obj._link:
            return '<a href="%s" target="_blank"><img src="http://graph.facebook.com/%s/picture" /></a>' % (obj._link, obj.id)
        else:
            return '<img src="http://graph.facebook.com/%s/picture" />' % (obj.id)
    profile_link.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        obj.get_from_facebook(save=True)
admin.site.register(User, UserAdmin)