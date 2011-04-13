#coding=utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _
from facebook.utils import get_graph
from django.conf import settings
from feinheit.translations import short_language_code

import logging
from django.template.loader import render_to_string
from django import forms
from akw.cleverreach import insert_new_user
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
                     ('Registration', _('Registration')),
                     ('Addtab', _('Add to page')),
)

class PluginBase(object):
    def __init__(self, parent):
        self.context = {}
        self.parent = parent
        
        
class Likebox(PluginBase):
    def get_context(self, request, signed_request, *args, **kwargs):
        try:
            page = signed_request['page']['id']
        except KeyError:
            page = None
        graph = get_graph(request)
        pagegraph = graph.get_object(page)
        logger.info('graph: %s' %pagegraph)
        url = pagegraph['link']
        self.context.update({'url' : url })
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
    
    def subscribe(self, registration):
         group_id = groups['nl_de'] if short_language_code() == 'de' else groups['nl_fr']
         insert_new_user(registration, group_id, activated=True, sendmail=False)
    
    def get_context(self, signed_request, *args, **kwargs):
        if getattr(signed_request, 'registration', None):
            registration = signed_request['registration']
            registration.update({'facebook_id': signed_request['user_id']})
            result = self.subscribe(registration)
            self.context.update({'registered': True})
        else: 
            context.update({'registered': False})
        return context

class SocialPluginContent(models.Model):
    """ A Facebook Social Plugin that connects to the page where the tab is shown. """
    
    type = models.CharField(_('Plugin'), max_length=16, choices=AVAILABLE_PLUGINS)
    
    def __init__(self, *args, **kwargs):
        super(SocialPluginContent, self).__init__(*args, **kwargs)
        if self.type:
            self.social_context = self.SocialContext(self.type, self)
            logger.info('social_context %s' %self.social_context)
    
    @classmethod
    def initialize_type(cls, DIMENSION_CHOICES=None, use_parent_page=True):
        if DIMENSION_CHOICES is not None:
            cls.add_to_class('dimension', models.CharField(_('dimension'),
                max_length=10, blank=True, null=True, choices=DIMENSION_CHOICES,
                default=DIMENSION_CHOICES[0][0]))
        if not use_parent_page:
            cls.add_to_class('url', models.URLField(_('url'), blank=True, null=True, 
                                    help_text=_('URL to like/recommend. If you want the current URL, leave it blank. For the Like Box, give the correct URL to the Facebook Page'))
            )
            
    def SocialContext(self, className, *args, **kwargs):
        aClass = getattr(__import__(__name__, fromlist=['contents']), className)
        return aClass (*args)                      
            
    def clean(self):
        super(SocialPluginContent, self).clean()
        if getattr(self.social_context, 'clean', None):
            self.social_context.clean()
        
 
    class Meta:
        abstract = True
        verbose_name = _('Facebook Social Plugin')
        verbose_name_plural = _('Facebook Social Plugins')

    @property
    def media(self):
        media = forms.Media()
        media.add_js(('http://connect.facebook.net/%s/all.js#xfbml=1' % FACEBOOK_LOCALES.get(short_language_code()),))
        return media
    
    def render(self, request, context, **kwargs):
        session = request.session.get('facebook', dict())
        try:
            signed_request = session['signed_request']
        except KeyError:
            logger.debug('No signed_request in current session.')
            signed_request = {}
        context = {}
        context.update(self.social_context.get_context(request=request, signed_request=signed_request))
       
        if self.dimension:
            context.update({'dimensions' : self.dimension.split('x')})
        return render_to_string('content/facebook/%s.html' % self.type, context)
    