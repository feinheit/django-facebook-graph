# -*- coding: utf-8 -*-
""" To use any of those models, add facebook.connections to your INSTALLED_APPS. """

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from facebook.models import User, Page
from facebook.utils import get_graph
from datetime import datetime
        
        
class Like(models.Model):
    """ The users likes. Uses a generic foreign key to Page so it doesn't need
        a Page instance but you still get all the ORM goodness.
    """
    user = models.ForeignKey(User)
    _name = models.CharField(_('Name'), max_length=255, blank=True)
    _category = models.CharField(_('Name'), max_length=255, blank=True)
    # Using the contenttype framework because of database integrity.
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    content_id = models.BigIntegerField(_('Liked page id'), blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'content_id')
    _created_time = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Like')
        verbose_name_plural = _('Likes')
    
    def __unicode__(self):
        return u'%s likes %s' % (self.user, self._name)
    
    @property
    def _id(self):
        return self.content_id
    
    @_id.setter
    def _id(self, value):
        self.content_type = ContentType.objects.get_for_model(Page)
        self.content_id = value
    
    @property
    def created_time(self):
        return self._created_time
    
    @created_time.setter
    def created_time(self, val):
        if '+' in val: # ignore timezone for now ...
                        val = val[:-5]
        self._created_time = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")