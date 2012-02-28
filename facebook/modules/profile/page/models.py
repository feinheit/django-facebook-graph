# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _
from facebook.fields import JSONField
from facebook.graph import get_graph, GraphAPIError

from facebook.modules.profile.models import Profile

class Page(Profile):
    # Cached Facebook Graph fields for db lookup
    _likes = models.IntegerField(blank=True, null=True, help_text=_('Cached fancount of the page'))
    _access_token = models.CharField(max_length=255, blank=True, null=True)
    _category = models.CharField(_('category'), max_length=255, blank=True, null=True)
    _location = JSONField(_('location'), blank=True, null=True)
    _phone = models.CharField(_('phone'), max_length=255, blank=True, null=True)
    _checkins = models.IntegerField(_('checkins'), blank=True, null=True)
    _website = models.URLField(_('website'), blank=True, null=True)
    _talking_about_count = models.PositiveIntegerField(_('talking about count'), blank=True, null=True)

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

    def get_from_facebook(self, graph=None, save=False, args=None):
        """ Updates the local fields with data from facebook. Use this function."""
        if not graph:
            graph = get_graph()
        target = str(self._id)
        if args:
            target = '%s?%s' % (target, args)
        try:
            response = graph.request(target)
        except GraphAPIError:
            logger.warning('Error in GraphAPI')
            if save:
                self.save()
            return None
        else:
            if response and save:
                if 'logo_url' in response.keys():
                    self._pic_square = response['logo_url']
                    self._picture = response['logo_url']
                self.save_from_facebook(response)

            elif save:
                self._graph = {'django-facebook-error' : 'The query returned nothing. Maybe the object is not published, accessible?',
                               'response': response,
                               'access_token': graph.access_token }
                self.save()
            else:
                return response
    
    class Facebook:
        public_fields = ['id', 'name', 'picture', 'link', 'category', 'likes', 'location', 'phone', 'checkins', 
                         'website', 'username', 'founded', 'products']
        member_fields = []
        connections = ['feed', 'posts', 'tagged', 'statuses', 'links', 'notes', 'photos', 'albums', 'events', 'videos']
        type = 'page'
