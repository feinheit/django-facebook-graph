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
    id = models.BigIntegerField(primary_key=True, unique=True)
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
        # _to should not be stored in the database because it is ambiguous
        to = self._to
        self._to = None
        super(Request, self).save(*args, **kwargs)
        self._to = to

    def delete(self, facebook=True, graph=None, to=None, app_name=None, *args, **kwargs):
        """
        One app request can have several to users. So it has to be deleted
        individually for every user. Either by passing the current user as to
        argument or a user graph when calling the delete method.

        :param facebook: Deprecated. Deletes request on Facebook as well.
        :param graph: Graph instance. User Graph required if to is not given.
        :param to: Request to. Usually the current user.
        :param app_name:
        :param args:
        :param kwargs:
        :return: Nothing
        """
        if to or self._to:
            if not graph:
                graph = get_graph(request=None, app_name=app_name)
            return graph.delete_object(u'%s_%s' % (self.id, to.id if to else self._to_id))
        elif graph and graph.type == 'user':
            return graph.delete_object(str(self.id))
        else:
            return super(Request, self).delete(facebook=False, *args, **kwargs)


    def get_from_facebook(self, graph=None, save=settings.DEBUG, quick=False):
        """ Only saves the request to the db if DEBUG is True."""
        if quick and self._from:
            # _to is not defined.
            self._to = None
            return self
        return super(Request, self).get_from_facebook(graph=graph, save=True)
