from facebook.utils import get_graph
from feincms.module.page.models import Page


def get_application_from_request(request):
    try:
        page = Page.objects.from_request(request, best_match=True)
        return getattr(page, 'facebook_application', None)
    except Page.DoesNotExist:
        return None
    
def get_application_graph_from_request(request):
    app = get_application_from_request(request)
    
    if app:
        return get_graph(client_secret=app.secret, client_id=app.id)
    else:
        return None

def get_page_from_request(request):
    try:
        page = Page.objects.from_request(request, best_match=True)
        return getattr(page, 'facebook_page', None)
    except Page.DoesNotExist:
        return None

def get_tab_url_from_request(request):
    try:
        page = Page.objects.from_request(request, best_match=True)
    except Page.DoesNotExist:
        return None
    
    fb_app = getattr(page, 'facebook_application', None)
    fb_page = getattr(page, 'facebook_page', None)

    if fb_page and fb_app:
        if '?' in fb_page.facebook_link:
            separator = '&'
        else:
            separator = '?'
        return u'%s%ssk=app_%s' % (fb_page.facebook_link, separator, fb_app.id)
    else:
        return None
