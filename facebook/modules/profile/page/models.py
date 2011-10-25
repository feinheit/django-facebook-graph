# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from facebook.modules.profile.models import Profile

class Page(Profile):
    # Cached Facebook Graph fields for db lookup
    _likes = models.IntegerField(blank=True, null=True, help_text=_('Cached fancount of the page'))
    _access_token = models.CharField(max_length=255, blank=True, null=True)

    @property
    def name(self):
        return self._name

    @property
    def picture(self):
        return self._picture

    @property
    def fan_count(self):
        return self._likes

    @property
    def facebook_link(self):
        return self._link

    def __unicode__(self):
        return '%s (%s)' % (self._name, self.id)
    
    class Facebook:
        public_fields = ['id', 'name', 'picture', 'link', 'category', 'likes', 'location', 'phone', 'checkins', 
                         'website', 'username', 'founded', 'products']
        member_fields = []
        connections = ['feed', 'posts', 'tagged', 'statuses', 'links', 'notes', 'photos', 'albums', 'events', 'videos']
        type = 'page'
