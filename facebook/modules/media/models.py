# -*- coding: utf-8 -*-
from django.db import models
from facebook.modules.base import Base
from facebook.modules.profile.user.models import User
from facebook.graph import get_graph
from django.utils.translation import ugettext_lazy as _

class Photo(Base):
    fb_id = models.BigIntegerField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='uploads/')
    message = models.TextField(_('message'), blank=True)

    # Cached Facebook Graph fields for db lookup
    _name = models.CharField(max_length=100, blank=True, null=True)
    # TODO: Use through Like Model.
    _likes = models.ManyToManyField(User, related_name='photo_likes')
    _like_count = models.PositiveIntegerField(blank=True, null=True)
    _from_id = models.BigIntegerField(null=True, blank=True)

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

