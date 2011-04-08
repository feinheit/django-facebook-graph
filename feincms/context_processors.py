from utils import get_tab_url_from_request

def facebook_tab_deeplink(request):
    tab_url = get_tab_url_from_request(request)
    return {'facebook_tab_deeplink' : '%s&app_data=%s' % (tab_url, request.path_info) }