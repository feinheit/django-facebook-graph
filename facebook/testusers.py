#coding=utf-8
from facebook.models import TestUser
from facebook.graph import GraphAPIError
from django.utils import simplejson


class TestUsers(object):
    def __init__(self, graph):
        self.graph = graph
    
    # Friend requests need user access token
    def update_access_token(self, access_token):
        self.graph.access_token = access_token

    def generate_new_test_user(self, installed=True, permissions=[]):
        response = self.graph.request('%s/accounts/test-users' % self.graph.app_id, None, 
                                      {'installed': installed, 'permissions': ', '.join(permissions) })
        user = TestUser()
        user.save_from_facebook(response, app_id=self.graph.app_id)
        return user

    def get_test_users(self, login_url_required=False):
        """ users is a dict array with the fields access_token, login_url and id. """
        response = self.graph.request('%s/accounts/test-users' % self.graph.app_id, 
                                      {'access_token': self.graph.access_token })['data'] 
        users=[]
        for item in response:
            # Facebook sometimes does not deliver a login-url. Ignore those users.
            try:
                testuser, created = TestUser.objects.get_or_create(id=item['id'], 
                                defaults={'id': item['id'], 'login_url': item['login_url'],
                                          'belongs_to': self.graph.app_id,
                                          '_graph': simplejson.dumps(item) })
                if created:
                    testuser.save_from_facebook(item, app_id=self.graph.app_id)
                else:
                    testuser.login_url = item['login_url']
                    testuser._graph = simplejson.dumps(item)
                testuser.save()
                users.append(testuser)
            except KeyError:
                pass
                
            
        # cleanup db
        users_ids=[int(i['id']) for i in response]
        testusers = TestUser.objects.select_related(depth=1).filter(belongs_to=self.graph.app_id)
        for user in testusers:
            if user.id not in users_ids:
                user.delete()
            elif not user._name and user.access_token:
                self.graph.access_token = user.access_token
                response = user.get_from_facebook(graph=self.graph, save=True)
        return testusers
    
    def friend_request(self, user1, user2):
        graph = self.graph
        graph.access_token = user1.access_token
        return graph.request('%s/friends/%s' % (user1.id, user2.id), None, {})
    
    def make_friends_with(self, user1, user2):
        response = []
        self.update_access_token(user1.access_token)
        try:
            response.append(self.friend_request(user1, user2))
        except GraphAPIError as error:  #No access token if the user is not authorized.
            response.append(error)
        self.update_access_token(user2.access_token)
        try:
            response.append(self.friend_request(user2, user1))
        except GraphAPIError as error:
            response.append(error)
        return response
    
    def unfriend(self, user1, user2):
        pass
