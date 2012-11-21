# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
try:
    from django.utils import timezone
except ImportError:
    #can only be used for timezone.now()
    from datetime import datetime as timezone

from datetime import timedelta

from facebook.modules.base import Base
from facebook.modules.profile.user.models import User
from facebook.graph import get_graph, GraphAPIError


FACEBOOK_APPS_CHOICE = tuple((v['ID'], unicode(k)) for k,v in settings.FACEBOOK_APPS.items())

class RequestManager(models.Manager):
    def get_query_set(self):
        killerdate = timezone.now()-timedelta(days=14)
        return super(RequestManager, self).get_query_set().filter(created__gte=killerdate)


class Request(Base):
    """ App request model. Must be deleted manually by the app."""
    # The request id consists of the request id and the to id. <REQUEST_OBJECT_ID>_<USER_ID>
    id = models.CharField(primary_key=True, max_length=65, unique=True)
    # Cached Facebook Graph fields for db lookup
    _application_id = models.BigIntegerField('Application', choices=FACEBOOK_APPS_CHOICE, blank=True, null=True)
    _to = models.ForeignKey(User, blank=True, null=True, related_name='request_to_set')
    _from = models.ForeignKey(User, blank=True, null=True, related_name='request_from_set')
    _data = models.TextField(blank=True, null=True)
    _message = models.TextField(blank=True, null=True)
    _created_time = models.DateTimeField(blank=True, null=True)

    objects = RequestManager()
    
    class Meta:
        app_label = 'facebook'
        abstract = False
    
    def __unicode__(self):
        try:
            return u'%s from %s: to %s: data: %s' % (self.id, self._from_id, self._to_id, self._data)
        except models.FieldDoesNotExist:
            return u'%s' % self.id

    def save(self, *args, **kwargs):
        if not self._to and '_' in self.id:
            request_id = self.id.split('_')
            to, created = User.objects.get_or_create(id=int(request_id[1]))
            self._to = to
        elif not '_' in self.id and self._to:
            self.id = "%s_%s" % (self.id, self._to)
        super(Request, self).save(*args, **kwargs)
    
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
