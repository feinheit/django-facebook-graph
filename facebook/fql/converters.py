from django.core.serializers.json import DjangoJSONEncoder
from facebook import fb
import datetime

class ConverterBase(object):
    """ This class converts a FQL JSON string into a GRAPH JSON string """

    def timestamp2iso(self, timestamp):
        return datetime.datetime.utcfromtimestamp(timestamp).isoformat()


class PostConverter(ConverterBase):
    """ https://developers.facebook.com/docs/reference/fql/stream/

        since = datetime.datetime.now()-datetime.timedelta(days=10)
        limit = 2
        since = int(totimestamp(since))
        query = {"query1":
                 "SELECT source_id, post_id, actor_id, message, updated_time, created_time, app_data, \
                 action_links, attachment, comments, likes, permalink, app_id, attribution, filter_key \
                 FROM stream WHERE source_id = 204147462938788",
                 "query2": \
                 "SELECT name, id FROM profile WHERE id IN (SELECT source_id FROM #query1)",
                 "query3": \
                 "SELECT object_id, post_id, fromid, time, text, id, post_fbid, likes, comments \
                 FROM comment WHERE post_id IN (SELECT post_id FROM #query1)"}
    """

    def guess_type(self, fql):
        if fql.get('attachment').get('description') == '' and fql.get('app_data') == []:
            return 'post'
        elif fql.get('app_data') and fql['app_data'].get('attachment_data', False):
            return 'link'
        elif fql.get('attachment') and fql['attachment'].get('fb_object_type') == 'album':
            return 'photo'
            
            

    def to_graph(self, fql_response):
        graph_response = []
        for fql in fql_response:
            graph = {}
            graph['id'] = fql.get('post_id', '')
            graph['from'] = {'id': fql.get('actor_id', None)}
            graph['to'] = fql.get('target_id', None)
            graph['message'] = fql.get('message', '')
            try:
                attachment = fql['attachment']
                graph['name'] = attachment['name']
            except (AttributeError, KeyError):
                pass
            else:
                try:
                    graph['picture'] = attachment['media'][0]['src']
                except (AttributeError, IndexError):
                    pass
                graph['link'] = attachment.get('href', '')
                graph['caption'] = attachment.get('caption', '')
                graph['description'] = attachment.get('description', '')
                graph['icon'] = attachment.get('icon', '')
            graph['likes'] = fql.get('likes')
            graph['comments'] = fql.get('comments')
            graph['application'] = {'id': fql.get('app_id', ''), 'name': fql.get('attribution', '')}
            graph['created_time'] = self.timestamp2iso(fql.get('created_time'))
            graph['updated_time'] = self.timestamp2iso(fql.get('updated_time'))
            graph['type'] = self.guess_type(fql)

            graph_response.append(graph)

        return graph_response
