import hashlib

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.template.defaultfilters import slugify

import facebook
from facebook.models import User as FacebookUser
from facebook.utils import get_graph


@transaction.commit_on_success
def get_or_create_user(username, defaults):
    """
    Hopefully a bit safer version of User.objects.get_or_create

    Thanks, StackOverflow:

    http://stackoverflow.com/questions/2235318/how-do-i-deal-with-this-race-condition-in-django
    """
    try:
        user = User.objects.create(username=username, **defaults)
    except IntegrityError: # Probably a duplicate?
        transaction.commit()
        user = User.objects.get(username=username)
    return user


class AuthenticationBackend(object):
    supports_anonymous_user = False

    def authenticate(self, uid=None, graph=None):
        if not graph:
            raise AttributeError, 'Authentication Backend needs a valid graph.'

        profile = graph.me

        try:
            facebook_user = FacebookUser.objects.get(id=uid)
            facebook_user.access_token = graph.access_token
            facebook_user.get_from_facebook(graph=graph, save=True)
            if isinstance(facebook_user.user, User):
                return facebook_user.user
        
        except ObjectDoesNotExist:
            facebook_user = FacebookUser(id=uid)
            facebook_user.get_from_facebook(graph=graph, save=True)

        user = get_or_create_user(slugify(profile['id']), {
                'email': profile.get('email', u''),
                'first_name': profile.get('first_name', u''),
                'last_name': profile.get('last_name', u''),
                'password': hashlib.md5(uid).hexdigest(),
                })

        facebook_user.user = user
        facebook_user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except:
            return None