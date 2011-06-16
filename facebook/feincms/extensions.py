from django.db import models
from django.utils.translation import ugettext_lazy as _

from facebook.models import Application, Page


def facebook_application(cls, admin_cls):
    cls.add_to_class('facebook_application', models.ForeignKey(Application, blank=True, null=True, help_text=_('Link this page to a facebook app. Used for Facebook Tabs, to determine the underlaying FB App')))
    cls.add_to_class('facebook_page', models.ForeignKey(Page, blank=True, null=True, related_name='facebook_page_set', help_text=_('Link this page to a facebook page. Used for Facebook Tabs, to determine the underlaying FB Page and prevent the Tab to be added to a random foreign page')))

    admin_cls.fieldsets.append((_('Facebook Application'),{
        'fields' : ('facebook_application', 'facebook_page',),
        'classes' : ('collapse',),
    }))


def content_type_extension(cls, admin_cls=None):
    """ Monkeypatch for content types. a patched content type will only render its content dependent of these settings
    Sample implementation (models.py):

    from facebook.feincms.extensions import content_type_extension
    content_type_extension(Page.create_content_type(RichTextContent))
    """
    RENDER_CHOICES = (
        (0, _('both')),
        (1, _('true')),
        (2, _('false')),
    )

    # save the original render method
    cls.original_render = cls.render

    cls.add_to_class('render_like', models.PositiveSmallIntegerField(_('render like'), blank=True, null=True, default=0, choices=RENDER_CHOICES, help_text=_('Render this content only, if requesting user likes the page.')))
    cls.add_to_class('app_installed', models.PositiveSmallIntegerField(_('app installed'), blank=True, null=True, default=0, choices=RENDER_CHOICES, help_text=_('Render this content only, if requesting user has installed the corresponding app.')))

    def render(instance, request, context, **kwargs):
        """ override render function. renders on dependency of the render settings. """

        try:
            # will crash, if there is no facebook and/or signed request in the session
            user_liked = request.session['facebook']['signed_request']['page']['liked']
        except:
            return instance.original_render(**kwargs)

        try:
            # if the user has not installed the app, there will be no user_id
            user_id = request.session['facebook']['signed_request']['user_id']
            app_installed = True
        except:
            app_installed = False

        render_because_of_like = True
        render_because_of_app_installed = True

        if (instance.render_like == 2 and user_liked) or \
            (instance.render_like == 1 and not user_liked):
            render_because_of_like = False

        if (instance.app_installed == 2 and app_installed) or \
            (instance.app_installed == 1 and not app_installed):
            render_because_of_app_installed = False

        if render_because_of_like and render_because_of_app_installed:
            return instance.original_render(**kwargs)
        else:
            return '<!-- content not rendered because of facebook params -->'
    cls.render = render
