# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings

from facebook.modules.base import Base
from facebook.modules.profile.user.models import User
from facebook.graph import get_graph, GraphAPIError


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
    
    
    class Meta:
        app_label = 'facebook'
        abstract = False
    
    def __unicode__(self):
        return u'%s from %s: to %s: data: %s' % (self._id, self._from, self._to, self._data)
    
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
        super(Request, self).get_from_facebook(graph=graph, save=True)
    
