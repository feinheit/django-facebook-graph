from django.http import HttpResponse
from django.http import HttpResponseBadRequest

from facebook.utils import get_graph

from models import User

def input(request, action):
    """ method to save a graph-object query, that is retrieved client side """
    
    json = request.POST.get('json', None)
    
    graph = get_graph(request)
    
    if action == 'user':
        if json:
            user, created = User.objects.get_or_create(id=json['id'])
    
            user.access_token = graph.access_token
            user.save_from_facebook(json)
        else:
            user, created = User.objects.get_or_create(id=graph.user)
            user.get_from_facebook(request)
            user.access_token = graph.access_token
            user.save()
        
        return HttpResponse('ok')
    
    elif action == 'friends':
        if json == None:
            return HttpResponseBadRequest('Facebook Graph JSON response is required as "json" attribute')
        
        user, created = User.objects.get_or_create(id=graph.user)
        user.save_friends(json)
        
        return HttpResponse('ok')
    
    elif action == 'user-friends-once':
        user, created = User.objects.get_or_create(id=graph.user)
        if created or not user.access_token:
            user.get_friends(save=True, request=request)
        user.access_token = graph.access_token
        user.get_from_facebook(request)
        user.save()
        
        return HttpResponse('ok')
    
    return HttpResponseBadRequest('action %s not implemented' % action)