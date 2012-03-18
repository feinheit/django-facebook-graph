from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from facebook.modules.base import Base

class Milestone(Base):
    id = models.BigIntegerField(primary_key=True)
    # from is a Generic FK to User or Page.
    _from = generic.GenericForeignKey('__profile_type', '__profile_id')
    __profile_id = models.BigIntegerField()
    __profile_type = models.ForeignKey(ContentType)
    _created_time = models.DateTimeField(blank=True, null=True)
    _updated_time = models.DateTimeField(blank=True, null=True)
    _start_time = models.DateTimeField(blank=True, null=True)
    _end_time = models.DateTimeField(blank=True, null=True)
    _title = models.CharField(max_lenght=255, blank=True, null=True)
    _description = models.TextField()
    
    class Meta:
        ordering = ['-_start_time']
        get_latest_by = '_start_time'
        verbose_name = _('Milestone')
        verbose_name_plural = _('Milestones')
    
    def __unicode__(self):
        return self.title