from feincms.module.page.models import Page

def get_application_from_request(request):
    try:
        page = Page.objects.best_match_for_path(request.path)
        return getattr(page, 'facebook_application', None)
    except Page.DoesNotExist:
        return None
