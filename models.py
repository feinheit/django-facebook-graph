import logging
logger = logging.getLogger(__name__)

<<<<<<< HEAD
from django import forms
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
=======
from datetime import datetime

from django.contrib.auth.models import User as DjangoUser
>>>>>>> e326d935d2e4d5d921add8a11a57371c8c7265ad
from django.db import models
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _


from fields import JSONField
from utils import get_graph

class Base(models.Model):
    """ Last Lookup JSON """
    _graph = models.TextField(blank=True, null=True)
    
    @property
    def graph(self):
        return json.loads(self._graph)
    
    created = models.DateTimeField(editable=False, default=datetime.now)
    updated = models.DateTimeField(editable=False, default=datetime.now)
    
    class Meta:
        abstract = True
        
    def get_from_facebook(self, save=False, request=None, access_token=None, \
             client_secret=None, client_id=None):
        
        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)
        response = graph.request(str(self.id))
        
        if response and save:
            self.save_from_facebook(response)
        if response:
            self._graph = json.dumps(response, cls=DjangoJSONEncoder)
            for prop, (val) in response.items():
                if hasattr(self, '_%s' % prop):
                    setattr(self, '_%s' % prop, val)
            return response
        else:
            logger.debug('graph not retrieved', extra=response)
            return None
    
    def save_from_facebook(self, json):
        self._graph = json
        for prop, (val) in json.items():
            if hasattr(self, '_%s' % prop):
                setattr(self, '_%s' % prop, val)
        self.save()
    
    def clean(self, refresh=True, request=None, access_token=None, \
             client_secret=None, client_id=None, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.now()
        self.updated = datetime.now()
        
        if self._graph:
            try:
                self._graph = json.dumps(json.loads(self._graph), cls=DjangoJSONEncoder)
            except ValueError:
                raise forms.ValidationError(_('Invalid JSON Data'))
        
        if refresh:
            self.refresh(request=request, access_token=access_token, \
                        client_secret=client_secret, client_id=client_id, \
                        *args, **kwargs)

class User(Base):
    id = models.BigIntegerField(primary_key=True, unique=True)
    access_token = models.CharField(max_length=250, blank=True)
    user = models.OneToOneField(DjangoUser, blank=True, null=True)
    
    """ Cached Facebook Graph fields for db lookup"""
    _first_name = models.CharField(max_length=50, blank=True, null=True)
    _last_name = models.CharField(max_length=50, blank=True, null=True)
    _name = models.CharField(max_length=100, blank=True, null=True)
    _link = models.URLField(verify_exists=False, blank=True, null=True)
    _birthday = models.DateField(blank=True, null=True)
    _email = models.EmailField(blank=True, null=True)
    _location = models.CharField(max_length=70, blank=True, null=True)
    _gender = models.CharField(max_length=10, blank=True, null=True)
    _locale = models.CharField(max_length=6, blank=True, null=True)
    
    friends = models.ManyToManyField('self')
    
    def __unicode__(self):
        return '%s (%s)' % (self._name, self.id)
    
    def get_friends(self, save=False, request=None, access_token=None, \
             client_secret=None, client_id=None):
        
        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)
        response = graph.request('%s/friends' % self.id)
        friends = response['data']
        
        if save:
            self.save_friends(friends)
        
        return friends
    
    def save_friends(self, friends):
        for jsonfriend in friends:
            friend, created = User.objects.get_or_create(id=jsonfriend['id'])
            if created:
                friend._name = jsonfriend['name']
                friend.save()
            all_friends = list(self.friends.all().values_list('id'));
            if not friend in all_friends:
                self.friends.add(friend)
        self.save()
        return friends
