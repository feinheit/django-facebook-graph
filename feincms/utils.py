from feincms.module.page.models import Page

def get_application_from_request(request):
    try:
        page = Page.objects.best_match_for_path(request.path)
        return getattr(page, 'facebook_application', None)
    except Page.DoesNotExist:
        return None

def get_page_from_request(request):
    try:
        page = Page.objects.best_match_for_path(request.path)
        return getattr(page, 'facebook_page', None)
    except Page.DoesNotExist:
        return None

def get_tab_url_from_request(request):
    fb_page = get_page_from_request(request)
    fb_app = get_application_from_request(request)

    if fb_page and fb_app:
        return u'%s?sk=app_%s' % (fb_page.facebook_link, fb_app.id)
