# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from facebook.fields import JSONField
from facebook.modules.base import Base
from facebook.modules.profile.user.models import User
from facebook.graph import get_graph, get_static_graph, GraphAPIError


FACEBOOK_APPS_CHOICE = tuple((v['ID'], unicode(k)) for k,v in settings.FACEBOOK_APPS.items())

class Request(Base):
    """ App request model. Must be deleted manually by the app."""
    id = models.BigIntegerField(primary_key=True, unique=True)
    
    # Cached Facebook Graph fields for db lookup
    _application_id = models.BigIntegerField('Application', max_length=30, choices=FACEBOOK_APPS_CHOICE, blank=True, null=True)
    _to = models.ForeignKey(User, blank=True, null=True, related_name='request_to_set')
    _from = models.ForeignKey(User, blank=True, null=True, related_name='request_from_set')
    _data = models.TextField(blank=True, null=True)
    _message = models.TextField(blank=True, null=True)
    _created_time = models.DateTimeField(blank=True, null=True)
    
    def delete(self, facebook=True, graph=None, app_name=None, *args, **kwargs):
        if not graph:
            graph = get_graph(request=None, app_name=app_name) # Method needs static graph
        try:
            super(Request, self).delete(facebook=facebook, graph=graph, *args, **kwargs)
        except GraphAPIError:
            graph = get_graph(request=None, app_name=app_name)
            try:
                super(Request, self).delete(facebook=facebook, graph=graph, *args, **kwargs)
            except GraphAPIError:
                super(Request, self).delete(facebook=False, graph=None, *args, **kwargs)

    def get_from_facebook(self, graph=None, save=settings.DEBUG, quick=True):
        """ Only saves the request to the db if DEBUG is True."""
        if quick and save and self._graph:
            return self
        if not graph:
            graph = get_graph() # get app graph only
        super(Request, self).get_from_facebook(graph=graph, save=True)
    
    def __unicode__(self):
        return u'%s from %s: to %s: data: %s' % (self._id, self._from, self._to, self._data)
    
    

class Score(models.Model):
    """ The score object stores a game score for a user. It is automatically
        posted in the user's activity feed. 
        To get or set scores use the app access token.
    """
    user = models.ForeignKey(User)
    score = models.PositiveIntegerField(_('Score'))
    application_id = models.BigIntegerField(_('Application'), max_length=30, choices=FACEBOOK_APPS_CHOICE, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Score')
        verbose_name_plural = _('Scores')
        ordering = ['-score']
        
    class Facebook:
        access_token_type = 'app'
        type = 'score'
    
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
        
        
class Achievment(models.Model):
    id = models.BigIntegerField(primary_key=True)
    title = models.CharField(_('Title'), max_length=255)
    url = models.URLField(_('url'))
    description = models.CharField(_('Description'), max_length=255)
    image = JSONField(_('image'), blank=True)
    points = models.SmallIntegerField(_('Points'))
    updated_time = models.DateTimeField(_('updated_time'), auto_now=True)
    context = JSONField(_('context'), blank=True)
    
    class Meta:
        verbose_name = _('Achievment')
        verbose_name_plural = _('Achievments')
        
    class Facebook:
        type = 'games.achievement'
    
    def __unicode__(self):
        return unicode(self.title)
    