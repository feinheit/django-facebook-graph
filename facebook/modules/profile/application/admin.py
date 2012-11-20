from django.contrib import admin

from facebook.modules.base import AdminBase
from facebook.modules.profile.application.models import Request

class RequestAdmin(AdminBase):
    list_display = ('id', '_application_id', '_to', '_from', '_data', '_message', '_created_time')
    readonly_fields = ('_graph', '_application_id', '_to', '_from', '_data', '_message', '_created_time')

admin.site.register(Request, RequestAdmin)