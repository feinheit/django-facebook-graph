import hashlib

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

import facebook
from facebook.models import FacebookUser

class AuthenticationBackend:
    def authenticate(self, uid=None, access_token=None):
        try:
            graph = facebook.GraphAPI(access_token)
            profile = graph.get_object("me")
        except facebook.GraphAPIError:
            return None
        
        try:
            facebook_user = FacebookUser.objects.get(id=uid)
            facebook_user.access_token = access_token
            facebook_user.save()
            user = facebook_user.user
        except ObjectDoesNotExist:
            facebook_user = FacebookUser(id=uid, profile_url=profile["link"], access_token=access_token)
            user, created = User.objects.get_or_create(username=profile["name"], email=profile["email"], password=hashlib.md5(uid).hexdigest())
            facebook_user.user = user
            facebook_user.save()
        
        return user
    
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except:
            return None