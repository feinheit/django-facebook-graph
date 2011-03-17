import logging
logger = logging.getLogger(__name__)

from django import forms
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
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
    
    class Meta:
        abstract = True
        
    def refresh(self, save=True, *args, **kwargs):
        graph = get_graph()
        response = graph.request(str(self.id))
        
        if response:
            self._graph = json.dumps(response, cls=DjangoJSONEncoder)
            for prop, (val) in response.items():
                if hasattr(self, '_%s' % prop):
                    setattr(self, '_%s' % prop, val)
        else:
            logger.debug('graph not retrieved', extra=response)
        
        if save: 
            self.save()
        return self
    
    def clean(self, refresh=True, request=None, access_token=None, \
             client_secret=None, client_id=None, *args, **kwargs):
        if self._graph:
            try:
                self._graph = json.dumps(json.loads(self._graph), cls=DjangoJSONEncoder)
            except ValueError:
                raise forms.ValidationError(_('Invalid JSON Data'))
        
        if refresh:
            self.refresh(request=request, access_token=access_token, \
                        client_secret=client_secret, client_id=client_id, \
                        *args, **kwargs)

class FacebookUser(Base):
    id = models.BigIntegerField(primary_key=True, unique=True)
    access_token = models.CharField(max_length=250, blank=True)
    user = models.OneToOneField(User, blank=True, null=True)
    
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
    
    """ Last Lookup JSON """
    _graph = JSONField(blank=True, null=True)
    
    @property
    def graph(self):
        return self._graph
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return '%s (%s)' % (self._name, self.id)
