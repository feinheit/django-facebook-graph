#coding=utf-8
from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import escapejs
register = template.Library()

@register.simple_tag(takes_context=True)
def user_var(context):
    """ Adds the user informations from the FB signed request to Google Analytics.
        You need to put this tag before the _trackPageview call.
    """
    request = context.get('request')
    try:
        age = request.session['facebook']['signed_request']['user']['age']
        page = request.session['facebook']['signed_request']['page']['id']
        locale = request.session['facebook']['signed_request']['user']['locale']
    except (AttributeError, KeyError):
        return mark_safe('<!-- no signed request -->')
    
    response = "_gaq.push(['_setCustomVar', 1, 'Age', '%s', 2]);\n" % escapejs(age)
    response += "_gaq.push(['_setCustomVar', 2, 'fb-page', '%s', 1]);\n " % page
    response += "_gaq.push(['_setCustomVar', 3, 'fb-locale', '%s', 1]);\n" % locale
    return mark_safe(response)