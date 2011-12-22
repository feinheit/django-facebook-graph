# -*- coding: utf-8 -*-
""" To use any of those models, add facebook.connections to your INSTALLED_APPS. """

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from facebook.modules.profile.user.models import User
from facebook.modules.profile.page.models import Page

        
class Like(models.Model):
    """ The users likes. Uses a generic foreign key to Page so it doesn't need
        a Page instance but you still get all the ORM goodness.
    """
    user = models.ForeignKey(User)
    _name = models.CharField(_('Name'), max_length=255, blank=True)
    _category = models.CharField(_('Name'), max_length=255, blank=True)
    # Using the contenttype framework because of database integrity.
    # object type is usually profile or photo.
    object_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.BigIntegerField(_('Liked page id'), blank=True, null=True)
    content_object = generic.GenericForeignKey('object_type', 'object_id')
    # This field exists in the facebook table. But does not seem to be serverd by the graph api.
    post_id = models.CharField(_('Post id'), max_length=255, blank=True, null=True)
    _created_time = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Profile Like')
        verbose_name_plural = _('Profile Likes')
        app_label = 'facebook'
    
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

    
class URLLike(models.Model):
    """ This model can be used when querying the url_like table. """
    user = models.ForeignKey(User)
    url = models.URLField(_('URL'), max_length=500, verify_exists=False, blank=True, null=True)
    
    class Meta:
        verbose_name = _('URL Like')
        verbose_name_plural = _('URL Likes')
        app_label = 'facebook'
        
    def __unicode__(self):
        return unicode(self.url)
    

