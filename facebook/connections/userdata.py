from django.http import Http404, HttpResponse

from facebook.models import User as FBUser
from facebook.utils import get_graph
import facebook
from models import Like

from datetime import datetime

# Find a JSON parser
try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

_parse_json = lambda s: json.loads(s)

def get_likes(request):
    if 'data' in request.POST:
        data = _parse_json(request.POST.get('data'))
        user, created = FBUser.objects.get_or_create(id=int(data.get('id', 0 )))
        graph = get_graph(request)
        user.get_from_facebook(graph=graph, save=True)
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
            like, c = Like.objects.get_or_create(user=user, content_id=int(entry.get('id',0)))
            
            like._name = entry.get('name', '')
            like._category = entry.get('category', '')
            like._id = entry.get('id', None )
            like._created_time = created_time
            like.save()
        
        return HttpResponse('thank you')
    return HttpResponse('no data: %s' % request.POST)