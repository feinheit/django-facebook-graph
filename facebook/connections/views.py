from django.http import Http404, HttpResponse

import facebook
from models import Like

from datetime import datetime


def get_likes(graph, fb_user):
    # TODO: Also query URL Likes.
    if graph.type == 'app':
        raise AttributeError, 'Need user graph for get_likes.'
    try:
        response = graph.request('me/likes')
    except facebook.GraphAPIError as e:
        return HttpResponse('no permission: %s' % e)
    
    likes = response['data']
    for entry in likes:
        val = entry.get('created_time', None)
        if val:
            if '+' in val: # ignore timezone for now ...
                val = val[:-5]
            created_time = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
        else:
            created_time = datetime.now()
        like, c = Like.objects.get_or_create(user=fb_user, content_id=int(entry.get('id',0)))
        
        like._name = entry.get('name', '')
        like._category = entry.get('category', '')
        like._id = entry.get('id', None )
        like._created_time = created_time
        like.save()
    return True