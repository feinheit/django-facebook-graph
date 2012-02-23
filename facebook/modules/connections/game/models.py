from django.db import models
from django.utils.translation import ugettext_lazy as _

from facebook.fields import JSONField
from facebook.modules.base import Base
from facebook.modules.profile.user.models import User

class Score(Base):
    """ The score object stores a game score for a user. It is automatically
        posted in the user's activity feed.
        To get or set scores use the app access token.
    """
    _user = models.ForeignKey(User)
    _score = models.PositiveIntegerField(_('Score'))
    _application = JSONField(_('Application'), blank=True, null=True)
    _type = models.CharField(max_length=100, blank=True, null=True)

    class Meta(Base.Meta):
        verbose_name = _('Score')
        verbose_name_plural = _('Scores')
        ordering = ['-_score']

    class Facebook:
        access_token_type = 'app'
        type = 'score'

    def __unicode__(self):
        return u'%s, %s' % (self._user, self._score)


class Achievement(Base):
    """
    https://developers.facebook.com/docs/achievements/
    """
    id = models.BigIntegerField(primary_key=True)
    points = models.SmallIntegerField(_('Points'), blank=True, null=True)

    _type = models.CharField(max_length=50, default='games.achievement')
    _title = models.CharField(_('Title'), max_length=255, blank=True, null=True)
    _url = models.URLField(_('url'), blank=True, null=True)
    _description = models.CharField(_('Description'), max_length=255, blank=True, null=True)
    _image = JSONField(_('image'), blank=True)
    _data = JSONField(_('data'), blank=True)
    _updated_time = models.DateTimeField(_('updated_time'), auto_now=True)
    _context = JSONField(_('context'), blank=True)

    class Meta(Base.Meta):
        verbose_name = _('Achievement')
        verbose_name_plural = _('Achievements')

    class Facebook:
        type = 'games.achievement'

    def __unicode__(self):
        return unicode(self._title)
