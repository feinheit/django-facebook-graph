# -*- coding: utf-8 -*-
""" To use any of those models, add facebook.connections to your INSTALLED_APPS. """

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from facebook.models import User, Page
from facebook.utils import get_graph
from datetime import datetime



class Score(models.Model):
    """ The score object stores a game score for a user. It is automatically
        posted in the user's activity feed. """
    user = models.ForeignKey(User)
    score = models.PositiveIntegerField(_('Score'))
    
    class Meta:
        verbose_name = _('Score')
        verbose_name_plural = _('Scores')
        ordering = ['-score']
    
    def __unicode__(self):
        return u'%s, %s' % (self.user, self.score)
    
    def send_to_facebook(self, app_name=None, graph=None):
        if not graph:
            graph = get_graph(request=None, app_name=app_name)
        if self.score < 0:
            raise AttributeError, 'The score must be an integer >= 0.'
        return graph.request('%s/scores' % self.user.id ,'', {'score': str(self.score) })

    def save(self, facebook=True, app_name=None, graph=None, *args, **kwargs):
        super(Score, self).save(*args, **kwargs)
        if facebook:
            return self.send_to_facebook(app_name=app_name, graph=graph) 

    def delete(self, app_name=None, *args, **kwargs):
        graph = get_static_graph(app_name=app_name)
        graph.request('%s/scores' % self.user.id, post_args={'method': 'delete'})
        super(Score, self).delete(*args, **kwargs)
        
        
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