from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from facebook.models import Base


class Profile(Base):
    """ Base Class for user, group, page, event and application. """
    id = models.BigIntegerField(primary_key=True, unique=True, help_text=_('The ID is the facebook page ID'))
    _name = models.CharField(max_length=200, blank=True, null=True)
    _link = models.URLField(max_length=255, verify_exists=False, blank=True, null=True)
    _picture = models.URLField(max_length=500, blank=True, null=True, verify_exists=False, help_text=_('Cached picture of the page'))
    _pic_square = models.URLField(max_length=500, blank=True, null=True, verify_exists=False, editable=False)
    _pic_small = models.URLField(max_length=500, blank=True, null=True, verify_exists=False, editable=False)
    _pic_large = models.URLField(max_length=500, blank=True, null=True, verify_exists=False, editable=False)
    _pic_crop = models.URLField(max_length=500, blank=True, null=True, verify_exists=False, editable=False)

    class Meta:
        abstract = True

    @property
    def username(self):
        return self.slug

    @username.setter
    def username(self, name):
        self.slug = slugify(name)