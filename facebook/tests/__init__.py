from facebook.tests.utils import *
from facebook.models import TestUser

class TestUsers(object):
    def __init__(self, graph):
        self.graph = graph

    def generate_new_test_user(self, installed=True, permissions=[]):
        response = self.graph.request('%s/accounts/test-users' % self.graph.app_id, None, {'installed': installed, 'permissions': ', '.join(permissions) })
        user = TestUser()
        user.save_from_facebook(response)
        return user

    def get_test_users(self):
        users = self.graph.request('%s/accounts/test-users' % self.graph.app_id, {'access_token': self.graph.access_token }) 
        # TODO: Batch update login_url and access_token
    
    
    def make_friend_request(self, user1, user2):
        graph = self.graph
        graph.access_token = user1.access_token
        return graph.request('%s/friends/%s' % (user1.id, user2.id), None, {})
    
    def make_friends_with(self, user1, user2):
        return make_friend_request(user1, user2) and make_friend_request(user2, user1)