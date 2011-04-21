from django.shortcuts import render_to_response

from utils import get_page_from_request, get_tab_url_from_request


class PreventForeignApp(object):
    """ Checks the signed_request for the facebook page id. if it detects a foreign tab
    or an app, it redirects using a javascript redirection to the deeplink of the tab in the
    associated page """
    
    def process_request(self, request):
        if 'facebook' in request.session and 'signed_request' in request.session['facebook']:
            facebook_page = get_page_from_request(request)
            signed_request = request.session['facebook']['signed_request']
            
            if not facebook_page or not 'page' in signed_request:
                return None

            if signed_request['page']['id'] != str(facebook_page.id):
                destination = '%s&app_data=%s' % (get_tab_url_from_request(request), request.path_info)
                return render_to_response('redirecter.html', {'destination' : destination})
