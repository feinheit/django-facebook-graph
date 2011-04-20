import logging
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta

from django import forms
from django.db import models
from django.db import transaction
from django.contrib.auth.models import User as DjangoUser
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from facebook import GraphAPIError

from fields import JSONField
from utils import get_graph, post_image, get_FQL


class Base(models.Model):
    # Last Lookup JSON
    _graph = JSONField(blank=True, null=True)

    slug = models.SlugField(unique=True, blank=True, null=True)

    created = models.DateTimeField(editable=False, default=datetime.now)
    updated = models.DateTimeField(editable=False, default=datetime.now)

    class Meta:
        abstract = True

    @property
    def _id(self):
        """ the facebook object id for inherited functions """
        return self.id

    @property
    def graph_url(self):
        return 'http://graph.facebook.com/%s' % self._id
    
    @property
    def graph(self):
        return self._graph
    
    @property
    def cached(self):
        cached_fields = {}
        fieldnames = self._meta.get_all_field_names()
        for field in fieldnames:
            if field.find('_') == 0:
                cached_fields.update({field[1:] : getattr(self, field)})
        return cached_fields
    
    @property
    def refreshed_graph(self):
        """ updates the object from facebook and returns then the retrieved graph.
        bullet proof to use in templates: if the request times out or the answer is bad, the old graph is returned"""
        response = self.get_from_facebook()
        if response:
            self.save_from_facebook(response)
        return self._graph

    def get_from_facebook(self, save=False, request=None, access_token=None, \
             client_secret=None, client_id=None):

        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)
        try:
            response = graph.request(str(self._id))
            if response and save:
                self.save_from_facebook(response)
            elif save:
                self._graph = {'django-facebook-error' : 'The query returned nothing. Maybe the object is not published, accessible?'}
                self.save()
            else:
                return response
        except GraphAPIError:
            logger.warning('Error in GraphAPI')
            if save:
                self.save()
            return None

    def save_from_facebook(self, response, update_slug=False):
        """ update the local model with the response (JSON) from facebook 
        big magic in here: it tries to convert the data from facebook in appropriate django fields inclusive foreign keys"""

        self._graph = json.dumps(response, cls=DjangoJSONEncoder)
        for prop, (val) in response.items():
            field = '_%s' % prop
            if prop != 'id' and hasattr(self, field):
                fieldclass = self._meta.get_field(field)
                if isinstance(fieldclass, models.DateTimeField):
                    # reading the facebook datetime string. assuming we're in MET Timezone
                    # TODO: work with real timezones
                    setattr(self, field, datetime.strptime(val[:-5], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=7) )
                    
                elif isinstance(self._meta.get_field(field), models.ForeignKey):
                    # trying to build the ForeignKey and if the foreign Object doesnt exists, create it.
                    # todo: check if the related model is a facebook model (not sure if there are other possible relations ...) 
                    related_modelclass = fieldclass.related.parent_model
                    obj, created = related_modelclass.objects.get_or_create(id=val['id'])
                    setattr(self, field, obj)
                    if created:
                        obj.get_from_facebook(save=True)
                    
                else:
                    setattr(self, field, val)
            if prop == 'from' and hasattr(self, '_%s_id' % prop):
                setattr(self, '_%s_id' % prop, val['id'])

        # try to generate a slug, but only the first time (because the slug should be more persistent)
        if not self.slug or update_slug:
            try:
                self.slug = slugify(self._name)[:50]
            except:
                self.slug = self.id
        self.save()
    
    
    def save_to_facebook(self, target, graph=None):
        if not graph: graph=get_graph()
        
        args = {}
        cached_fields = [cached for cached in self._meta.get_all_field_names() if cached.find('_') == 0]
        for fieldname in cached_fields:
            fieldclass = self._meta.get_field(fieldname)
            field = getattr(self, fieldname)
            
            if field:
                if isinstance(fieldclass, models.DateField):
                    args[fieldname[1:]] = field.isoformat()
                elif isinstance(fieldclass, JSONField):
                    args[fieldname[1:]] = json.dumps(field)
                else:
                    args[fieldname[1:]] = field
        
        response = graph.put_object(str(target), self.Facebook.publish, **args)
        return response
    
    def get_connections(self, connection_name, graph, save=False):
        response = graph.request('%s/%s' % (self._id, connection_name))
        connections = response['data']

        if save:
            self.save_connections(connection_name, connections)
        return connections

    #@transaction.commit_manually
    def save_connections(self, connection_name, connections):
        model_connection_config = None
        connection_config = None
        if hasattr(self, 'Facebook') and hasattr(self.Facebook, 'connections'):
            model_connection_config = self.Facebook.connections
        
        if connection_name in self._meta.get_all_field_names():
            connecting_field_name = connection_name
        elif connection_name in model_connection_config:
            connection_config = model_connection_config[connection_name]
            connecting_field_name = connection_config['field']
        else:
            raise ObjectDoesNotExist('The Facebook Model %s has no connection configured with the name "%s"' % (self.__class__, connection))
    
        connecting_field = getattr(self, connecting_field_name)
        connected_model = self._meta.get_field(connecting_field_name).rel.to
        connected_model_ids = connected_model.objects.all().values_list('id', flat=True)
        
        new_connected_model_jsons = [item for item in connections if item['id'] not in connected_model_ids]
        for new_model_json in new_connected_model_jsons:
            new_connected_object = connected_model(id=new_model_json['id'])
            new_connected_object.save_from_facebook(new_model_json)
        
        connecting_model = connecting_field.through
        for connection_json in connections:
            
            kwargs = {'%s_id' % connecting_field.source_field_name : self.id,
                      '%s_id' % connecting_field.target_field_name : connection_json['id']}
            connection_object, created = connecting_model.objects.get_or_create(**kwargs)
            
            if connection_config:
                extra_fields = []
                if 'filter' in connection_config:
                    extra_fields.extend(connection_config['filter'].keys())
                if 'extra_fields' in connection_config:
                    extra_fields.extend(connection_config['extra_fields'])
                for extra_field in extra_fields:
                    setattr(connection_object, extra_field, connection_json[extra_field])
            connection_object.save()
        #transaction.commit()

    def clean(self, refresh=True, request=None, access_token=None, \
            client_secret=None, client_id=None, *args, **kwargs):
       ''' On save, update timestamps '''
       if not self.id:
           self.created = datetime.now()
       self.updated = datetime.now()

    def __unicode__(self):
        if hasattr(self, '_name'):
            return '%s (%s)' % (self._name, self.id)
        else:
            return str(self.id)

# it crashes my python instance on mac os x without proper error message, so may we shoudn't use that handy shortcut
# maybe its only, that the admin should'nt use these computed fields
#    def __getattr__(self, name):
#        """ the cached fields (starting with "_") should be accessible by get-method """
#        if hasattr(self, '_%s' % name):
#            return getattr(self, '_%s' % name)
#        return super(Base, self).__getattr_(name)


class User(Base):
    id = models.BigIntegerField(primary_key=True, unique=True)
    access_token = models.CharField(max_length=250, blank=True)
    user = models.OneToOneField(DjangoUser, blank=True, null=True)

    # Cached Facebook Graph fields for db lookup
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
    
    class Facebook:
        pass

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

    @property
    def facebook_link(self):
        return self._link


class Photo(Base):
    fb_id = models.BigIntegerField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='uploads/')

    # Cached Facebook Graph fields for db lookup
    _name = models.CharField(max_length=100, blank=True, null=True)
    _likes = models.ManyToManyField(User, related_name='photo_likes')
    _like_count = models.PositiveIntegerField(blank=True, null=True)
    _from_id = models.BigIntegerField(null=True, blank=True)

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

    @property
    def facebook_link(self):
        return 'http://www.facebook.com/photo.php?fbid=%s' % self.id

    def send_to_facebook(self, object='me', save=False, request=None, access_token=None, \
             client_secret=None, client_id=None, message=''):

        graph = get_graph(request=request, access_token=access_token, \
                          client_secret=client_secret, client_id=client_id)

        response = post_image(graph.access_token, self.image.file, message, object=object)

        if save:
            self.fb_id = response['id']
            self.save()
        return response['id']


class Page(Base):
    id = models.BigIntegerField(primary_key=True, unique=True, help_text=_('The ID is the facebook page ID'))

    # Cached Facebook Graph fields for db lookup
    _name = models.CharField(max_length=255, blank=True, null=True, help_text=_('Cached name of the page'))
    _picture = models.URLField(max_length=500, blank=True, null=True, verify_exists=False, help_text=_('Cached picture of the page'))
    _likes = models.IntegerField(blank=True, null=True, help_text=_('Cached fancount of the page'))
    _link = models.CharField(max_length=255, blank=True, null=True)

    @property
    def name(self):
        return self._name

    @property
    def picture(self):
        return self._picture

    @property
    def fan_count(self):
        return self._likes

    @property
    def facebook_link(self):
        return self._link

    def __unicode__(self):
        return '%s (%s)' % (self._name, self.id)

    #@models.permalink
    #def get_absolute_url(self):
    #    return ('page', (), {'portal' : self.portal.slug, 'page' : self.slug})


class Application(Page):
    """ The Application inherits the Page, because every application has a Page """
    api_key = models.CharField(max_length=32, help_text=_('The applications API Key'))
    secret = models.CharField(max_length=32, help_text=_('The applications Secret'))


class Event(Base):
    id = models.BigIntegerField(primary_key=True, unique=True, help_text=_('The ID is the facebook event ID'))

    # Cached Facebook Graph fields for db lookup
    _owner = JSONField(blank=True, null=True)
    _name = models.CharField(max_length=200, blank=True, null=True)
    _description = models.TextField(blank=True, null=True)
    _start_time = models.DateTimeField(blank=True, null=True)
    _end_time = models.DateTimeField(blank=True, null=True)
    _location = models.CharField(max_length=200, blank=True, null=True)
    _venue = JSONField(blank=True, null=True)
    _privacy = models.CharField(max_length=10, blank=True, null=True, choices=(('OPEN', 'OPEN'), ('CLOSED', 'CLOSED'), ('SECRET', 'SECRET')))
    _updated_time = models.DateTimeField(blank=True, null=True)
    
    invited = models.ManyToManyField(User, through='EventUser')
    
    @property
    def facebook_link(self):
        return 'http://www.facebook.com/event.php?eid=%s' % self.id
    
    class Meta:
        ordering = ('_start_time',)
    
    class Facebook:
        connections = {'attending' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'attending'}},
                       'maybe' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'unsure'}},
                       'declined' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'declined'}},
                       'noreply' : {'field' : 'invited', 'filter' : {'rsvp_status' : 'not_replied'}},
                       'invited' : {'field' : 'invited', 'extra_fields' : ['rsvp_status',]},}
        publish = 'events'
    
    def save_rsvp_status(self, user_id, status):
        user, created = User.objects.get_or_create(id=user_id)
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
        self.save_rsvp_status(graph.user, status)
        return fb_response


class EventUser(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(User)
    rsvp_status = models.CharField(max_length=10, default="attending", 
                              choices=(('attending', _('attending')),
                                       ('unsure', _('unsure')),
                                       ('declined', _('declined')),
                                       ('not_replied', _('not_replied'))))
    
    class Meta:
        unique_together = [('event', 'user'),]


class Request(Base):
    id = models.BigIntegerField(primary_key=True, unique=True)
    
    # Cached Facebook Graph fields for db lookup
    _application = models.ForeignKey(Application, blank=True, null=True)
    _to = models.ForeignKey(User, blank=True, null=True, related_name='request_to_set')
    _from = models.ForeignKey(User, blank=True, null=True, related_name='request_from_set')
    _data = models.TextField(blank=True, null=True)
    _message = models.TextField(blank=True, null=True)
    _created_time = models.DateTimeField(blank=True, null=True)
    
    def delete(self, facebook=True, graph=None, *args, **kwargs):
        if facebook:
            if not graph: graph = get_graph()
            try:
                graph.delete_object(str(self.id))
            except GraphAPIError, e:
                logger.warning('DELETE Request failed: %s' % e)
        super(Request, self).delete(*args, **kwargs)
    
    def __unicode__(self):
        return u'%s from %s: to %s: data: %s' % (self._id, self._from, self._to, self._data)
    
