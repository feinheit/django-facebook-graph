from django.contrib import admin

from facebook.admin import AdminBase

from .models import Post


class PostAdmin(AdminBase):
    def picture_link(self, obj):
            return '<img src="%s" />' % (obj._picture)
    picture_link.allow_tags = True
    picture_link.short_description = u'picture'

    def icon_link(self, obj):
            return '<img src="%s" alt="%s" width="16" height="16"/>' % (obj._icon, obj._type)
    icon_link.allow_tags = True
    icon_link.short_description = u'icon'

    list_display = ('icon_link', 'id', '_from', '_message', '_type', 'picture_link')
    list_display_links = ('id',)
    readonly_fields = ('_graph', '_application', '_to', '_from', '_message', '_picture', '_subject',
                       '_properties', '_actions', '_privacy', '_likes', '_comments', '_targeting')
    date_hierarchy = '_updated_time'
    list_filter = ('_type',)
admin.site.register(Post, PostAdmin)