# -*- coding: utf-8 -*-
""" To use any of those models, add facebook.connections to your INSTALLED_APPS. """

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from facebook.fields import JSONField
from facebook.models import Base
from facebook.modules.profile.user.models import User
from facebook.modules.profile.page.models import Page

        
class Like(models.Model):
    """ The users likes. Uses a generic foreign key to Page so it doesn't need
        a Page instance but you still get all the ORM goodness.
    """
    user = models.ForeignKey(User)
    _name = models.CharField(_('Name'), max_length=255, blank=True)
    _category = models.CharField(_('Name'), max_length=255, blank=True)
    # Using the contenttype framework because of database integrity.
    # object type is usually profile or photo.
    object_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.BigIntegerField(_('Liked page id'), blank=True, null=True)
    content_object = generic.GenericForeignKey('object_type', 'object_id')
    # This field exists in the facebook table. But does not seem to be serverd by the graph api.
    post_id = models.CharField(_('Post id'), max_length=255, blank=True, null=True)
    _created_time = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Profile Like')
        verbose_name_plural = _('Profile Likes')
    
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

    
class URLLike(models.Model):
    """ This model can be used when querying the url_like table. """
    user = models.ForeignKey(User)
    url = models.URLField(_('URL'), max_length=500, verify_exists=False, blank=True, null=True)
    
    class Meta:
        verbose_name = _('URL Like')
        verbose_name_plural = _('URL Likes')
        
    def __unicode__(self):
        return unicode(self.url)
    

class PostBase(Base):
    POST_TYPES = (('status', _('Status message')),
              ('link', _('Link')),
              ('photo', _('Photo')),
              ('video', _('Video')),
              ('note', _('Note')),
              )

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

