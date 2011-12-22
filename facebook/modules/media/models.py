# -*- coding: utf-8 -*-
from django.db import models
from facebook.modules.base import Base
from facebook.modules.profile.user.models import User
from facebook.modules.connections.likes.models import Like
from facebook.graph import get_graph
from django.utils.translation import ugettext_lazy as _


class Tag(models.Model):
    to = models.ForeignKey(User)
    x = models.PositiveSmallIntegerField(_('x'), blank=True, null=True,
        help_text='x coordinate of tag, as a percentage offset from the left edge of the picture')
    y = models.PositiveSmallIntegerField(_('y'), blank=True, null=True,
        help_text='y coordinate of tag, as a percentage offset from the top edge of the picture ')
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
    
    def __unicode__(self):
        return u'Tag %s' % self.to


class Photo(Base):
    fb_id = models.BigIntegerField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='uploads/')
    message = models.TextField(_('message'), blank=True)

    # Cached Facebook Graph fields for db lookup
    _name = models.CharField(max_length=100, blank=True, null=True,
                help_text='The user provided caption given to this photo - do not include advertising in this field')
    _from = models.ForeignKey(User, blank=True, null=True, related_name='photos_uploaded',
                help_text='The profile (user or page) that posted this photo')
    _icon = models.URLField(_('icon'), blank=True, null=True,
                help_text='The icon that Facebook displays when photos are published to the Feed')
    _picture = models.URLField(_('picture'), blank=True, null=True,
                        help_text='The thumbnail-sized source of the photo')
    _source = models.URLField(_('source'), blank=True, null=True,
                        help_text='The full-sized source of the photo')
    _height = models.PositiveSmallIntegerField(_('height'), blank=True, null=True,
                        help_text='The height of the photo in pixels')
    _width = models.PositiveSmallIntegerField(_('width'), blank=True, null=True,
                        help_text='The width of the photo in pixels')
    _link = models.URLField(_('link'), blank=True, null=True,
                        help_text='A link to the photo on Facebook')
    _position = models.PositiveSmallIntegerField(_('position'), blank=True, null=True,
                        help_text='The position of this photo in the album')

    # TODO: Make sure ContentType is Photo.
    #_likes = models.ManyToManyField(Like, related_name='photo_likes')
    _like_count = models.PositiveIntegerField(blank=True, null=True)
    
    _tags = models.ManyToManyField(Tag, related_name='photo_tags')

    class Meta:
        abstract = False
        app_label = 'facebook'

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

