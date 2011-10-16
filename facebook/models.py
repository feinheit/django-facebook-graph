import logging
logger = logging.getLogger(__name__)

from datetime import datetime
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from facebook.graph import GraphAPIError, get_graph
from facebook.profile.user.models import User as FbUser

from fields import JSONField

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
        if hasattr(self, '_name') and self._name:
            return u'%s (%s)' % (self._name, self.id)
        else:
            return unicode(self.id)
    
    def delete(self, facebook=False, graph=None, *args, **kwargs):
        """ Deletes the local model and if facebook is true, also the facebook instance."""
        if facebook:
            if not graph: graph = get_graph()
            graph.delete_object(str(self.id))
        super(Base, self).delete(*args, **kwargs)
    delete.alters_data = True




# it crashes my python instance on mac os x without proper error message, so may we shoudn't use that handy shortcut
# maybe its only, that the admin should'nt use these computed fields
#    def __getattr__(self, name):
#        """ the cached fields (starting with "_") should be accessible by get-method """
#        if hasattr(self, '_%s' % name):
#            return getattr(self, '_%s' % name)
#        return super(Base, self).__getattr__(name)



POST_TYPES = (('status', _('Status message')),
              ('link', _('Link')),
              ('photo', _('Photo')),
              ('video', _('Video')),
              ('note', _('Note')),
              # Umfrage
)


class PostBase(Base):
    id = models.CharField(_('id'), max_length=40, primary_key=True)
    _from = models.ForeignKey(FbUser, blank=True, null=True, verbose_name=_('from'),
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

