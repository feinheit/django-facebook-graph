from django.contrib.contenttypes import generic
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from facebook.modules.base import Base, AdminBase


class Profile(Base):
    """ Base Class for user, group, page, event and application. """
    id = models.BigIntegerField(primary_key=True, unique=True, help_text=_('The ID is the facebook page ID'))
    _name = models.CharField(max_length=200, blank=True, null=True)
    _username = models.CharField(max_length=200, blank=True, unique=True, null=True)
    _link = models.URLField(max_length=255, blank=True, null=True)
    _picture = models.URLField(max_length=500, blank=True, null=True, help_text=_('Cached picture of the page'))
    _pic_square = models.URLField(max_length=500, blank=True, null=True, editable=False)
    _pic_small = models.URLField(max_length=500, blank=True, null=True, editable=False)
    _pic_large = models.URLField(max_length=500, blank=True, null=True, editable=False)
    _pic_crop = models.URLField(max_length=500, blank=True, null=True, editable=False)

    # get all posts for the selected profile
    #    posts = [p.post for p in page.post_throughs.select_related('post').all()]
    if 'facebook.modules.connections.post' in settings.INSTALLED_APPS:
        post_throughs = generic.GenericRelation('PagePost',
                            related_name="%(app_label)s_%(class)s_related")

    class Meta(Base.Meta):
        abstract = True
        app_label = 'facebook'

    def clean(self):
        super(Profile, self).clean()
        # Turn empty String into None for Uniqueness check.
        self._username = self._username or None


    def generate_slug(self):
        # username is unique on facebook, but not every object has a username (ie. user have to make themself for pages and profiles)
        if self._username:
            if len(self._username) >= 50:
                self.slug = '%s_%s' % (slugify(self._username)[:29], self.id)
            self.slug = slugify(self._username)[:50]
        elif self._name:
            self.slug = slugify('%s-%s' % (self._name[:29], self.id))
        else:
            self.slug = slugify(self.id)


class ProfileAdmin(AdminBase):

    def pic_img(self, obj):
        return '<img src="%s" height="75" />' % obj._picture if obj._picture else ''
    pic_img.allow_tags = True
    pic_img.short_description = _('Picture')
