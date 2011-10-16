# -*- coding: utf-8 -*-

from django.db import models
from facebook.profile import Profile
from facebook.profile.user.models import User as FbUser
from facebook.graph import get_graph
from facebook.fql import get_FQL
from django.db.models import Q
from datetime import datetime, timedelta, date

from facebook.fields import JSONField

class EventManager(models.Manager):
    def upcoming(self):
        """ returns all upcoming and ongoing events """
        today = date.today()
        if datetime.now().hour < 6:
            today = today-timedelta(days=1)
        
        return self.filter(Q(_start_time__gte=today) | Q(_end_time__gte=today))
    
    def past(self):
        """ returns all past events """
        today = date.today()
        if datetime.now().hour < 6:
            today = today-timedelta(days=1)
        
        return self.filter(Q(_start_time__lt=today) & Q(_end_time__lt=today))

class Event(Profile):
    # Cached Facebook Graph fields for db lookup
    _owner = JSONField(blank=True, null=True)
   
    _description = models.TextField(blank=True, null=True)
    _start_time = models.DateTimeField(blank=True, null=True)
    _end_time = models.DateTimeField(blank=True, null=True)
    _location = models.CharField(max_length=500, blank=True, null=True)
    _venue = JSONField(blank=True, null=True)
    _privacy = models.CharField(max_length=10, blank=True, null=True, choices=(('OPEN', 'OPEN'), ('CLOSED', 'CLOSED'), ('SECRET', 'SECRET')))
    _updated_time = models.DateTimeField(blank=True, null=True)
    
    invited = models.ManyToManyField(FbUser, through='EventUser')

    objects = EventManager()

    @property
    def facebook_link(self):
        return 'http://www.facebook.com/event.php?eid=%s' % self.id
    
    def get_description(self):
        return self._description
    
    def get_name(self):
        return self._name
    
    class Meta:
        ordering = ('_start_time',)
    
    class Facebook:  # TODO: refactoring here.
        connections = {'attending' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'attending'}},
                       'maybe' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'unsure'}},
                       'declined' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'declined'}},
                       'noreply' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'not_replied'}},
                       'invited' : {'field' : 'invited', 'extra_fields' : ['rsvp_status',]},}
        publish = 'events'
        arguments = ['name', 'start_time', 'end_time']
        type = 'event'
    
    def save_rsvp_status(self, user_id, status):
        user, created = FbUser.objects.get_or_create(id=user_id)
        if created:
            user.save()
        connection, created = self.invited.through.objects.get_or_create(user=user, event=self)
        connection.status = status
        connection.save()
        return connection
    
    def update_rsvp_status(self, user_id, access_token=None):
        if not access_token: access_token=get_graph().access_token
        response = get_FQL('SELECT rsvp_status FROM event_member WHERE uid=%s AND eid=%s' % (user_id, self.id),
                           access_token=access_token)
        if len(response):
            self.save_rsvp_status(user_id, response[0]['rsvp_status'])
            return response[0]['rsvp_status']
        else:
            return 'not invited'
    
    def respond(self, graph, status='attending'):
        fb_response = graph.put_object(str(self.id), status)
        self.save_rsvp_status(graph.user_id, status)
        return fb_response


class EventUser(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(FbUser)
    rsvp_status = models.CharField(max_length=10, default="attending", 
                              choices=(('attending', _('attending')),
                                       ('unsure', _('unsure')),
                                       ('declined', _('declined')),
                                       ('not_replied', _('not_replied'))))
    
    class Meta:
        unique_together = [('event', 'user'),]

