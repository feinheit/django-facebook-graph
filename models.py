import logging
from urllib import urlencode
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from django.conf import settings

from django import forms
from django.db import models
from django.db import transaction
from django.contrib.auth.models import User as DjangoUser
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from facebook import GraphAPIError

from fields import JSONField
from utils import get_graph, post_image


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
    
    def get_facebook_url(self):
        app_id = getattr(settings, 'FACEBOOK_APP_ID', '')
        path = self.get_absolute_url()
        if getattr(settings, 'FACEBOOK_REDIRECT_PAGE_URL', False):
            url = '%s?sk=app_%s&app_data=%s' % (settings.FACEBOOK_REDIRECT_PAGE_URL, app_id, urlencode(path))
            return url
        else:
            return path

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

    def save_from_facebook(self, response, update_slug=False):
        """ update the local model with the response (JSON) from facebook """

        self._graph = json.dumps(response, cls=DjangoJSONEncoder)
        for prop, (val) in response.items():
            field = '_%s' % prop
            if prop != 'id' and hasattr(self, field):
                if isinstance(self._meta.get_field(field), models.DateTimeField):
                    # reading the facebook datetime string. assuming we're in MET Timezone
                    # TODO: work with real timezones
                    setattr(self, field, datetime.strptime(val[:-5], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=7) )
                else:
                    setattr(self, field, val)
            if prop == 'from' and hasattr(self, '_%s_id' % prop):
                setattr(self, '_%s_id' % prop, val['id'])

        # try to generate a slug, but only the first time (because the slug should be more persistent)
        if not self.slug or update_slug:
            try:
                self.slug = slugify(self.name)[:50]
            except:
                self.slug = self.id
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

    def clean(self, refresh=True, request=None, access_token=None, \
            client_secret=None, client_id=None, *args, **kwargs):
       ''' On save, update timestamps '''
       if not self.id:
           self.created = datetime.now()
       self.updated = datetime.now()

    def __unicode__(self):
        return '%s (%s)' % (self._name, self.id)

# it crashes my python instance on mac os x without proper error message, so may we shoudn't use that handy shortcut
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

    @property
    def facebook_link(self):
        return 'http://www.facebook.com/event.php?eid=%s' % self.id

