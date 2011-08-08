import hashlib

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from django.template.defaultfilters import slugify

import facebook
from facebook.models import User as FacebookUser

class AuthenticationBackend(object):
    supports_anonymous_user = False

    def authenticate(self, uid=None, access_token=None):
        try:
            graph = facebook.GraphAPI(access_token)
            profile = graph.get_object("me")
        except facebook.GraphAPIError:
            return None

        try:
            facebook_user = FacebookUser.objects.get(id=uid)
            facebook_user.access_token = access_token
            facebook_user.save_from_facebook(profile)
            user = facebook_user.user
        except ObjectDoesNotExist:
            facebook_user = FacebookUser(id=uid,
                                         access_token=access_token)
            user, c = User.objects.get_or_create(
                                username=slugify(profile["id"]),  # must be unique
                                email=profile["email"],
                                password=hashlib.md5(uid).hexdigest())
            user.first_name = profile['first_name']
            user.last_name = profile['last_name']
            user.save()
            facebook_user.user = user
            facebook_user.save_from_facebook(profile)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except:
            return None