from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect

from feincms.module.page.models import Page


def redirect_to_slug(request):
    """ tries to redirect the user with help of the facebook signed_request page params (admin, liked) """

    try:
        facebook_page = request.session['facebook']['signed_request']['page']
    except KeyError as e:
        return HttpResponse('<!-- could not redirect to slug via facebook page signed request params: %s -->' % e)


    page = Page.objects.for_request(request, raise404=True, best_match=True)
    if facebook_page['admin'] and facebook_page['liked']:
        try:
            return redirect(page.get_children().filter(slug='admin-liked')[0])
        except IndexError:
            pass
    if facebook_page['liked']:
        try:
            return redirect(page.get_children().filter(slug='liked')[0])
        except IndexError:
            pass
    if facebook_page['admin']:
        try:
            return redirect(page.get_children().filter(slug='admin')[0])
        except IndexError:
            pass

    try:
        return redirect(page.get_children().filter(slug='unliked')[0])
    except IndexError:
        return HttpResponse('<!-- no childpage with matching slug found. looked for slugs: admin-liked, liked, admin, unliked -->')