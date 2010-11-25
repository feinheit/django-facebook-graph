import logging
logger = logging.getLogger(__name__)

from datetime import datetime

from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.db import transaction

from facebook import GraphAPIError

from fields import JSONField
from utils import get_graph, post_image

class Base(models.Model):
    """ Last Lookup JSON """
    _graph = JSONField(blank=True, null=True)
    
    created = models.DateTimeField(editable=False, default=datetime.now)
    updated = models.DateTimeField(editable=False, default=datetime.now)
    
    @property
    def graph(self):
        return self._graph
    
    class Meta:
        abstract = True
        
    def get_from_facebook(self, save=False, request=None, access_token=None, \
             client_secret=None, client_id=None):
        
        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)
        try:
            response = graph.request(str(self._id))
            if response and save:
                self.save_from_facebook(response)
            if response:
                return response
        except GraphAPIError:
            logger.warning('Error in GraphAPI')
            if save:
                self.save()
            return None
    
    def save_from_facebook(self, json):
        self._graph = json
        for prop, (val) in json.items():
            if prop != 'id' and hasattr(self, '_%s' % prop):
                setattr(self, '_%s' % prop, val)
            if prop == 'from' and hasattr(self, '_%s_id' % prop):
                setattr(self, '_%s_id' % prop, val['id'])
        self.save()
        
    
    def get_connections(self, connection, save=False, request=None, \
             access_token=None, client_secret=None, client_id=None):
        
        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)
        
        if connection == 'likes':
            response = graph.request('%s/likes' % self._id)
        
        connections = response['data']
        
        if save:
            self.save_connections(connection, connections)
        return connections
    
    @transaction.commit_manually
    def save_connections(self, connection, connections):
        if connection == 'likes':
            """ get all user ids """
            user_ids = [ str(u[0]) for u in User.objects.all().values_list('id') ]
            new_users = [liker for liker in connections if liker['id'] not in user_ids]
            for new_user in new_users:
                self._likes.create(id=new_user['id'], _name=new_user['name'])
                
            likers = [ str(u[0]) for u in self._likes.all().values_list('id') ]
            new_likers = [liker for liker in connections if liker['id'] not in likers]
            for new_liker in new_likers:
                user, created = User.objects.get_or_create(id=new_liker['id'])
                self._likes.add(user)
                self.save()
            transaction.commit()
    
    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.now()
        self.updated = datetime.now()
        super(Base, self).save(*args, **kwargs)

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
    
    @property
    def _id(self):
        """ the facebook object id for inherited functions """
        return self.id
    
    @property
    def name(self):
        return self._name
    
    @property
    def gender(self):
        return self._gender
    
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

class Photo(Base):
    fb_id = models.BigIntegerField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='uploads/')
    
    _name = models.CharField(max_length=100, blank=True, null=True)
    _likes = models.ManyToManyField(User, related_name='photo_likes')
    _like_count = models.PositiveIntegerField(blank=True, null=True)
    _from_id = models.BigIntegerField(null=True, blank=True)
    
    @property
    def _id(self):
        """ the facebook object id for inherited functions """
        return self.fb_id
    
    @property
    def like_count(self):
        self._like_count = self._likes.all().count()
        self.save()
        return self._like_count
    
    @property
    def name(self):
        return self._name
    
    @property
    def from_object(self):
        return self._from_id
    
    def send_to_facebook(self, object='me', save=False, request=None, access_token=None, \
             client_secret=None, client_id=None, message=''):
        
        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)
        
        response = post_image(graph.access_token, self.image.file, message, object=object)
        
        if save:
            self.fb_id = response['id']
            self.save()
        return response['id']