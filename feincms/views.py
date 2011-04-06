from django.shortcuts import redirect

from feincms.module.page.models import Page

def redirect_to_slug(request):
    """ tries to redirect the user with help of the facebook signed_request page params (admin, liked) """
    
    try:
        facebook_page = request.session['facebook']['signed_request']['page']
    except e:
        return '<!-- could not redirect to slug via facebook page signed request params: %s -->' % e
    
    page = Page.objects.best_match_for_path(request.path)
    if facebook_page['admin'] and facebook_page['liked']:
        try:
            return redirect(page.get_children().filter(slug='admin-liked')[0].get_absolute_url())
        except:
            pass
    if facebook_page['liked']:
        try:
            return redirect(page.get_children().filter(slug='liked')[0].get_absolute_url())
        except:
            pass
    if facebook_page['admin']:
        try:
            return redirect(page.get_children().filter(slug='admin')[0].get_absolute_url())
        except:
            pass
    
    try:
        return redirect(page.get_children().filter(slug='unliked')[0].get_absolute_url())
    except:
        return '<!-- no chlidpage with matching slug found. looked for slugs: admin-liked, liked, admin, unliked -->'