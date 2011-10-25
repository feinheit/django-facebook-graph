# -*- coding: utf-8 -*-
import warnings

from django.contrib.auth.models import User as DjangoUser
from django.db import models

from facebook.modules.profile.models import Profile


class UserBase(Profile):
    access_token = models.CharField(max_length=250, blank=True, null=True)
    user = models.OneToOneField(DjangoUser, blank=True, null=True, related_name='facebook%(class)s')

    # Cached Facebook Graph fields for db lookup
    _first_name = models.CharField(max_length=50, blank=True, null=True)
    _last_name = models.CharField(max_length=50, blank=True, null=True)
    _birthday = models.DateField(blank=True, null=True)
    _email = models.EmailField(blank=True, null=True, max_length=100)
    _location = models.CharField(max_length=70, blank=True, null=True)
    _gender = models.CharField(max_length=10, blank=True, null=True)
    _locale = models.CharField(max_length=6, blank=True, null=True)

    friends = models.ManyToManyField('self')
    
    class Meta:
        abstract=True
    
    class Facebook:
        public_fields = ['id', 'name', 'first_name', 'last_name', 'gender', 'locale', 'username']
        member_fields = ['link', 'third_party_id', 'updated_time', 'verified']
        type = 'user'

    def __unicode__(self):
        return u'%s (%s)' % (self._name, self.id)


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
    
    def picture_url(self, type='large'):
        if type not in ['large', 'small', 'square', 'crop']:
            raise AttributeError, 'type must be one of large, small, crop or square.'
        cached = getattr(self, '_pic_%s' % type, None)
        if cached:
            return cached
        else:
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
