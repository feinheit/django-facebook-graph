#coding=utf-8
from facebook.models import TestUser
from django.utils import simplejson


class TestUsers(object):
    def __init__(self, graph):
        self.graph = graph

    def generate_new_test_user(self, installed=True, permissions=[]):
        response = self.graph.request('%s/accounts/test-users' % self.graph.app_id, None, 
                                      {'installed': installed, 'permissions': ', '.join(permissions) })
        user = TestUser()
        user.save_from_facebook(response, app_id=self.graph.app_id)
        return user

    def get_test_users(self):
        """ users is a dict array with the fields access_token, login_url and id. """
        response = self.graph.request('%s/accounts/test-users' % self.graph.app_id, 
                                      {'access_token': self.graph.access_token })['data'] 
        users=[]
        for item in response:
            testuser, created = TestUser.objects.get_or_create(id=item['id'], 
                                defaults={'id': item['id'], 'login_url': item['login_url'],
                                          'belongs_to': self.graph.app_id,
                                          '_graph': simplejson.dumps(item) })
            testuser.save_from_facebook(item, app_id=self.graph.app_id)
            users.append(testuser)
        # cleanup db
        users_ids=[int(i['id']) for i in response]
        testusers = TestUser.objects.select_related(depth=1).filter(belongs_to=self.graph.app_id)
        for user in testusers:
            if user.id not in users_ids:
                user.delete()
            elif not user._name and user.access_token:
                self.graph.access_token = user.access_token
                response = user.get_from_facebook(graph=self.graph, save=True)
        return users
    
    def friend_request(self, user1, user2):
        graph = self.graph
        graph.access_token = user1.access_token
        return graph.request('%s/friends/%s' % (user1.id, user2.id), None, {})
    
    def make_friends_with(self, user1, user2):
        return make_friend_request(user1, user2) and make_friend_request(user2, user1)
    
    def unfriend(self, user1, user2):
        pass
