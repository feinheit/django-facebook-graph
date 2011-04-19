#coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _
from facebook.utils import get_graph, get_FQL
from facebook.models import Event
from django.conf import settings
from feinheit.translations import short_language_code

import logging
from django.template.loader import render_to_string
from django import forms
from django.template.defaultfilters import urlencode
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.base import TemplateSyntaxError
from django.http import Http404
logger = logging.getLogger(__name__)

FACEBOOK_LOCALES = {
    'en' : 'en_US',
    'de' : 'de_DE',
    'fr' : 'fr_FR',
    'it' : 'it_IT',
    'es' : 'es_LA',
    'pt' : 'pt_PT',
}

AVAILABLE_PLUGINS = (('Likebutton', _('Like Button')),
                     ('Likebox', _('Like Box')),
                     ('Newsletter', _('Newsletter')),
                     ('Addtab', _('Add to page')),
                     ('Events', _('Upcoming Events')),
)

class PluginBase(object):
    def __init__(self, parent):
        self.context = {}
        self.parent = parent
    
    #Raise an exception if the class is not overwritten:
    def get_context(self, *args, **kwargs):
        raise NotImplementedError, 'You need to define a get_context function in your class\n which returns the extended context.'
        
        
class Likebox(PluginBase):
    def get_context(self, request, signed_request, *args, **kwargs):
        try:
            page = signed_request['page']['id']
        except KeyError:
            page = None
        graph = get_graph(request)
        pagegraph = graph.get_object(page)
        logger.debug('graph: %s' %pagegraph)
        try:
            url = pagegraph['link']
        except TemplateSyntaxError:
            raise Http404, 'session expired.'
        self.context.update({'url' : url , 'page' : page })
        return self.context
    
    def clean(self):
        """ A Like box needs to have a URL to a Facebook Page to like. You can define a default in :setting:'FACEBOOK_CONNECTED_PAGE' """
        try:
            if not getattr(settings, 'FACEBOOK_CONNECTED_PAGE', None) and not self.parent.url:
                raise ValidationError(_('If you want to add a "Like Box", you have to specify the URL of the Facebook Page to like.'))
        except AttributeError:
            pass
          
          
class Addtab(PluginBase):
    
    def get_context(self, *args, **kwargs):
        api_key = settings.FACEBOOK_APP_API_KEY
        FACEBOOK_REDIRECT_PAGE_URL = settings.FACEBOOK_REDIRECT_PAGE_URL
        self.context.update({'api_key' : api_key, 'FACEBOOK_REDIRECT_PAGE_URL': FACEBOOK_REDIRECT_PAGE_URL})
        return self.context


class Newsletter(PluginBase):       
    
    def get_context(self, signed_request, *args, **kwargs):
        if getattr(signed_request, 'registration', None):
            registration = signed_request['registration']
            self.context.update({'registered': True})
        else: 
            self.context.update({'registered': False})
        return self.context
    
    def add_media(self, media):
        media.add_js(('lib/fancybox/jquery.fancybox-1.3.1.pack.js',))
        media.add_css({'all':('lib/fancybox/jquery.fancybox-1.3.1.css', )})


class Events(PluginBase):
    def get_context(self, request, *args, **kwargs):
        upcoming = Event.objects.upcoming()
        graph = get_graph(request)

        # TODO: this:
        """
        try:
            me = graph.user
            query = "SELECT eid, rsvp_status FROM event_member WHERE uid = %s" % me
            rsvp_events = get_FQL(query, graph.access_token)
            events = {}
            for e in rsvp_events:
                events.update({e['eid'].encode('utf-8'): e['rsvp_status'].encode('utf-8')})
            self.context.update({ 'rsvp_events' : events })
            logger.debug('rsvp_events: %s' %rsvp_events)
        except AttributeError:
            pass
        """
        self.context.update({'events': upcoming, 'access_token': graph.access_token })
        return self.context
    
    def add_media(self, media):
        media.add_js(('/static/facebook/events.js',))
        media.add_css({'all':('/static/facebook/events.css', )})

class SocialPluginContent(models.Model):
    """ A Facebook Social Plugin that connects to the page where the tab is shown. """
    
    type = models.CharField(_('Plugin'), max_length=16, choices=AVAILABLE_PLUGINS)
    title = models.CharField(_('Title'), max_length=30, blank=True)
    description = models.TextField(_('Description'), blank=True)
    
    
    def __init__(self, *args, **kwargs):
        super(SocialPluginContent, self).__init__(*args, **kwargs)
        if self.type:
            self.social_context = self.SocialContext(self.type, self)
            logger.debug('social_context %s' %self.social_context)
    
    @classmethod
    def initialize_type(cls, DIMENSION_CHOICES=None):
        if DIMENSION_CHOICES is not None:
            cls.add_to_class('dimension', models.CharField(_('dimension'),
                max_length=10, blank=True, null=True, choices=DIMENSION_CHOICES,
                default=DIMENSION_CHOICES[0][0]))

            
    def SocialContext(self, className, *args, **kwargs):
        aClass = getattr(__import__(__name__, fromlist=['contents']), className.capitalize())
        return aClass (*args)                      
            
    def clean(self):
        super(SocialPluginContent, self).clean()
        try:
            if getattr(self.social_context, 'clean', None):
                self.social_context.clean()
        except AttributeError:
            pass
        
 
    class Meta:
        abstract = True
        verbose_name = _('Facebook Social Plugin')
        verbose_name_plural = _('Facebook Social Plugins')

    @property
    def media(self):
        media = forms.Media()
        #media.add_js(('http://connect.facebook.net/%s/all.js#xfbml=1' % FACEBOOK_LOCALES.get(short_language_code()),))
        try:
            self.social_context.add_media(media)
        except AttributeError:
            pass
        return media
    
    def render(self, request, context, **kwargs):
        session = request.session.get('facebook', dict())
        try:
            signed_request = session['signed_request']
        except KeyError:
            logger.debug('No signed_request in current session.')
            signed_request = {}
        context = {'content': self}
        context.update(self.social_context.get_context(request=request, signed_request=signed_request))
       
        if self.dimension:
            context.update({'dimensions' : self.dimension.split('x')})
        template = 'content/facebook/%s.html' % self.type
        return render_to_string(template.lower() , context)


    