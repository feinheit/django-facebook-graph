from django.db import models
from django.utils.translation import ugettext_lazy as _

from facebook.models import Application


def facebook_application(cls, admin_cls):
    cls.add_to_class('facebook_application', models.ForeignKey(Application, blank=True, null=True, help_text=('Link this page to a facebook app. Used for Facebook Tabs, to determine the underlaying FB App')))
    
    admin_cls.fieldsets.append((_('Facebook Application'),{
        'fields' : ('facebook_application',),
        'classes' : ('collapse',),
    }))