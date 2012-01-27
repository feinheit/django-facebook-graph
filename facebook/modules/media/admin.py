from django.contrib import admin

from facebook.modules.base import AdminBase

from .models import Photo

class PhotoAdmin(AdminBase):
    list_display = ('_id', '_name', 'like_count', '_from')
    readonly_fields = ('fb_id', '_name', '_tags', '_graph', '_from', '_like_count',
                       '_icon', '_picture', '_source', '_height', '_width', '_link', '_position')

admin.site.register(Photo, PhotoAdmin)