import logging
from urllib import urlencode
import warnings
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta, date
from django.conf import settings
from django import forms
from django.db import models, transaction
from django.db.models import Q
from django.contrib.auth.models import User as DjangoUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from facebook import GraphAPIError
import re

from fields import JSONField
from utils import get_graph, post_image, get_FQL

FACEBOOK_APPS_CHOICE = tuple((v['ID'], unicode(k)) for k,v in settings.FACEBOOK_APPS.items())

class Base(models.Model):
    # Last Lookup JSON
    _graph = JSONField(blank=True, null=True)

    slug = models.SlugField(unique=True, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, default=datetime.now)
    updated = models.DateTimeField(auto_now=True, default=datetime.now)

    class Meta:
        abstract = True
        
    class Facebook:
        pass

    @property
    def _id(self):
        """ the facebook object id for inherited functions """
        return self.id

    @property
    def graph_url(self):
        return 'https://graph.facebook.com/%s' % self._id
    
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

    def get_from_facebook(self, graph=None, save=False, args=None):
        """ Updates the local fields with data from facebook. Use this function."""
        if not graph:
            graph = get_graph()
        target = str(self._id)
        if args:
            target = '%s?%s' % (target, args)
        try:
            response = graph.request(target)
            if response and save:
                self.save_from_facebook(response)
            elif save:
                self._graph = {'django-facebook-error' : 'The query returned nothing. Maybe the object is not published, accessible?',
                               'response': response,
                               'access_token': graph.access_token }
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
                    if '+' in val: # ignore timezone for now ...
                        val = val[:-5]
                    setattr(self, field, datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")) #  - timedelta(hours=7) 


                elif isinstance(self._meta.get_field(field), models.ForeignKey):
                    # trying to build the ForeignKey and if the foreign Object doesnt exists, create it.
                    # todo: check if the related model is a facebook model (not sure if there are other possible relations ...) 
                    related_modelclass = fieldclass.related.parent_model
                    obj, created = related_modelclass.objects.get_or_create(id=val['id'])
                    setattr(self, field, obj)
                    if created:
                        obj.get_from_facebook(save=True)
                elif isinstance(fieldclass, models.DateField):
                    # Check for Birthday:
                    setattr(self, field, datetime.strptime(val, "%m/%d/%Y").date())
                else:
                    setattr(self, field, val)
            if prop == 'from' and hasattr(self, '_%s_id' % prop):
                setattr(self, '_%s_id' % prop, val['id'])

        self.save()
    save_from_facebook.alters_data = True
     
    
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
                elif isinstance(fieldclass, models.FileField) or isinstance(fieldclass, models.ImageField):
                    raise NotImplementedError  # TODO: use code from image field here
                else:
                    args[fieldname[1:]] = field

        # graph.put_object("me", "feed", message="Hello, world")
        response = graph.put_object(parent_object=str(target), connection_name=self.Facebook.publish, **args)
        return response
    
    def save(self, *args, **kwargs):
        # try to generate a slug, but only the first time (because the slug should be more persistent)
        if not self.slug:
            try:
                if self._name:
                    self.slug = slugify(self._name)[:50]
                else:
                    self.slug = slugify(self.id)
            except:
                self.slug = self.id
        super(Base, self).save(*args, **kwargs)
    
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
            raise ObjectDoesNotExist('The Facebook Model %s has no connection configured with the name "%s"' % (self.__class__, connection_name))
    
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

    def clean(self, refresh=True, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = datetime.now()
        self.updated = datetime.now()

    def __unicode__(self):
        if hasattr(self, '_name'):
            return '%s (%s)' % (self._name, self.id)
        else:
            return str(self.id)
    
    def delete(self, facebook=False, graph=None, *args, **kwargs):
        """ Deletes the local model and if facebook is true, also the facebook instance."""
        if facebook:
            if not graph: graph = get_graph()
            graph.delete_object(str(self.id))
        try:
            # if the model is abstract, it cannot be saved, but thats ok
            super(Base, self).delete(*args, **kwargs)
        except: # AssertionError
            pass
    delete.alters_data = True


# it crashes my python instance on mac os x without proper error message, so may we shoudn't use that handy shortcut
# maybe its only, that the admin should'nt use these computed fields
#    def __getattr__(self, name):
#        """ the cached fields (starting with "_") should be accessible by get-method """
#        if hasattr(self, '_%s' % name):
#            return getattr(self, '_%s' % name)
#        return super(Base, self).__getattr_(name)


class UserBase(Base):
    id = models.BigIntegerField(primary_key=True, unique=True)
    access_token = models.CharField(max_length=250, blank=True, null=True)
    user = models.OneToOneField(DjangoUser, blank=True, null=True, related_name='facebook%(class)s')

    # Cached Facebook Graph fields for db lookup
    _first_name = models.CharField(max_length=50, blank=True, null=True)
    _last_name = models.CharField(max_length=50, blank=True, null=True)
    _name = models.CharField(max_length=100, blank=True, null=True)
    _link = models.URLField(verify_exists=False, blank=True, null=True)
    _birthday = models.DateField(blank=True, null=True)
    _email = models.EmailField(blank=True, null=True, max_length=100)
    _location = models.CharField(max_length=70, blank=True, null=True)
    _gender = models.CharField(max_length=10, blank=True, null=True)
    _locale = models.CharField(max_length=6, blank=True, null=True)

    friends = models.ManyToManyField('self')
    
    class Facebook:
        public_fields = ['id', 'name', 'first_name', 'last_name', 'gender', 'locale', 'username']
        member_fields = ['link', 'third_party_id', 'updated_time', 'verified']

    def __unicode__(self):
        return '%s (%s)' % (self._name, self.id)


    def get_friends(self, graph, save=False):
        """ this function needs a valid access token."""
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

    def save_from_facebook(self, response, update_slug=False):
        if 'access_token' in response.iterkeys():
            self.access_token = response['access_token']
        super(UserBase, self).save_from_facebook(response, update_slug)

    class Meta:
        abstract=True
    
    def picture_url(self, type='large'):
        if type not in ['large', 'small', 'square']:
            raise AttributeError, 'type must be one of large, small or square.'
        return u'https://graph.facebook.com/%s/picture?type=%s' % (self.id, type)

    @property
    def square_picture_url(self):
        return self.picture_url(type='square')
    
    @property
    def large_picture_url(self):
        return self.picture_url(type='large')
            
    def get_absolute_url(self):
        if self._link:
            return self._link
        else:
            return 'http://www.facebook.com/profile.php?id=%s' % self.id


class User(UserBase):
    class Meta:
        abstract=False


# This code is for backwards compability only. Will be removed with verison 1.1.
def user__facebookuser(self):
    warnings.warn('Stop using `user`, use `facebookuser` instead.',
    DeprecationWarning, stacklevel=2)
    return self.facebookuser
DjangoUser.user = property(user__facebookuser)



class Photo(Base):
    fb_id = models.BigIntegerField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='uploads/')
    message = models.TextField(_('message'), blank=True)

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

    def send_to_facebook(self, object='me', save=False, graph=None, message=None, app_name=None):

        if not graph:
            graph = get_graph(app_name=app_name)
        if not message:
            message = self.message

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
    _access_token = models.CharField(max_length=255, blank=True, null=True)
    # TODO:
    # format: { app_name, app_id, access_token }
    #access_token = JSONField(_('access token'), blank=True, null=True)

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
    
    class Facebook:
        public_fields = ['id', 'name', 'picture', 'link', 'category', 'likes', 'location', 'phone', 'checkins', 
                         'website', 'username', 'founded', 'products']
        member_fields = []
        connections = ['feed', 'posts', 'tagged', 'statuses', 'links', 'notes', 'photos', 'albums', 'events', 'videos']


    #@models.permalink
    #def get_absolute_url(self):
    #    return ('page', (), {'portal' : self.portal.slug, 'page' : self.slug})

"""
Applications are by default stored in the settings.

class Application(Page):
    # The Application inherits the Page, because every application has a Page
    api_key = models.CharField(max_length=32, help_text=_('The applications API Key'))
    secret = models.CharField(max_length=32, help_text=_('The applications Secret'))
"""    

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

class Event(Base):
    id = models.BigIntegerField(primary_key=True, unique=True, help_text=_('The ID is the facebook event ID'))

    # Cached Facebook Graph fields for db lookup
    _owner = JSONField(blank=True, null=True)
    _name = models.CharField(max_length=200, blank=True, null=True)
    _description = models.TextField(blank=True, null=True)
    _start_time = models.DateTimeField(blank=True, null=True)
    _end_time = models.DateTimeField(blank=True, null=True)
    _location = models.CharField(max_length=500, blank=True, null=True)
    _venue = JSONField(blank=True, null=True)
    _privacy = models.CharField(max_length=10, blank=True, null=True, choices=(('OPEN', 'OPEN'), ('CLOSED', 'CLOSED'), ('SECRET', 'SECRET')))
    _updated_time = models.DateTimeField(blank=True, null=True)
    
    invited = models.ManyToManyField(User, through='EventUser')

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
        self.save_rsvp_status(graph.user_id, status)
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


class TestUser(UserBase):
    login_url = models.URLField('Login URL', blank=True, max_length=160)
    password = models.CharField('Password', max_length=30, blank=True)
    belongs_to = models.BigIntegerField(_('Belongs to'), help_text=_('The app the testuser has been created with.'))
    
    def __unicode__(self):
        return 'Testuser: %s (%s)' % (self._email, self.id)
    
    def set_password(self, graph, new_password):
        if graph.request('%s' % self.id, None, {'password': new_password, 'access_token': graph.access_token }):
            self.password = new_password
            self.save()
    
    def save_from_facebook(self, response, update_slug=False, app_id=None):
        if app_id:
            self.belongs_to = int(app_id)
        if 'login_url' in response.keys():
            self.login_url = response['login_url']
        if 'password' in response.keys():
            self.password = response['password']
        if 'access_token' in response.keys():
            self.access_token = response['access_token']
        self.id = response['id']
        super(TestUser, self).save_from_facebook(response, update_slug)
        
    class Meta:
        verbose_name = _('Test user')
        verbose_name_plural = _('Test users')

POST_TYPES = (('status', _('Status message')),
              ('link', _('Link')),
              ('photo', _('Photo')),
              ('video', _('Video')),
              ('note', _('Note')),
              # Umfrage
)

class PostBase(Base):
    id = models.CharField(_('id'), max_length=40, primary_key=True)
    _from = models.ForeignKey(User, blank=True, null=True, verbose_name=_('from'),
                              related_name='%(app_label)s_%(class)s_posts_sent')
    _to = JSONField(_('to'), blank=True, null=True)  # could be M2M but nees JSON processor.
    _message = models.TextField(_('message'), blank=True)
    _picture = models.URLField(_('picture url'), max_length=255, blank=True)
    _link = models.URLField(_('link url'), max_length=255, blank=True)
    _name = models.CharField(_('link name'), max_length=255, blank=True)
    _caption = models.CharField(_('link caption'), max_length=255, blank=True)
    _description = models.TextField(_('link description'),null=True, blank=True)
    _source = models.URLField(_('movie source'), max_length=255, blank=True)
    _properties = JSONField(_('movie properties'), blank=True, null=True)
    _icon = models.URLField(_('icon'), blank=True)
    _actions = JSONField(_('actions'), blank=True, null=True)
    _privacy = JSONField(_('privacy'), blank=True, null=True)
    _type = models.CharField(_('type'), max_length=20, choices=POST_TYPES, default='status')
    _likes = JSONField(_('likes'), blank=True, null=True)
    _comments = JSONField(_('comments'), blank=True, null=True) #denormalized
    _object_id = models.BigIntegerField(_('object id'), blank=True, null=True)  #generic FK to image or movie
    _application = JSONField(_('application'), blank=True, null=True)
    _created_time = models.DateTimeField(_('created time'), blank=True, null=True)
    _updated_time = models.DateTimeField(_('updated time'), blank=True, null=True)
    _targeting = JSONField(_('targeting'), blank=True, null=True)
    _subject = models.CharField(_('subject'), blank=True, max_length=255)

    class Meta:
        abstract=True
        
    class Facebook:
        publish = 'feed'
        connections = {'likes': None, 'comments': None }  # TODO: Create models for reference
        arguments = ['message', 'picture', 'link', 'name', 'caption', 'description', 'source', 'actions', 'privacy']

    def __unicode__(self):
        return u'%s, %s %s' % (self.id, self._message[:50], self._picture)

    # Note has no type attribute.
    def get_from_facebook(self, graph=None, save=False, *args, **kwargs):
        super(PostBase, self).get_from_facebook(graph=graph, save=True, *args, **kwargs)
        if self._subject:
            self._type = 'note'
        elif not self._type:
            self._type = 'status'
        self.save()
    
    def get_post_uid(self):
        ids = self.id.split('_')
        return ids[-1]
    
    @property
    def comments(self):
        return self._comments.get('data', [])
    
    @property
    def to(self):
        return self._to.get('data')[0]
    
    @property
    def actions(self):
        return dict((a['name'], a) for a in self._actions)
    
    @property
    def like_link(self):
        if self._link:
            return self._link
        elif self.actions.get('Like', False):
            return self.actions['Like']['link']
        elif self._type == 'note':
            return u'http://www.facebook.com/note.php?note_id=%s' % self.id
        else:
            try:
                return self.get_absolute_url()
            except AttributeError:
                return ''

class Post(PostBase):

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        abstract = False


class Score(models.Model):
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
    
    
    
    
