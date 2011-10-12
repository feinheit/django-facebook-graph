import hashlib

from django.contrib.auth.models import User, UNUSABLE_PASSWORD
from django.db import IntegrityError, transaction
from django.template.defaultfilters import slugify

import facebook
from facebook.models import User as FacebookUser
from facebook.utils import get_graph
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

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

    def authenticate(self, graph=None):
        if not graph:
            raise AttributeError, 'Authentication Backend needs a valid graph.'
   
        # check if the access token is valid:
        try:
            me = graph.request('me')
        except facebook.GraphAPIError as e:
            logger.debug('Could not authenticate User: %s ' % e)
            return None
        
        try:
            facebook_user = FacebookUser.objects.get(id=int(me['id']))
        except FacebookUser.DoesNotExist:
            facebook_user = FacebookUser(id=int(me['id']))
            facebook_user.get_from_facebook(graph=graph, save=True)
        else:
            try:
                if isinstance(facebook_user.user, User) and facebook_user.user.is_authenticated():
                    return facebook_user.user
            except User.DoesNotExist:
                pass
        #we use the Facebook id as username because 'me.name' is not unique enough.
        user = get_or_create_user(me['id'], {
                'email': me.get('email', u''),
                'first_name': me.get('first_name', u''),
                'last_name': me.get('last_name', u''),
                'password': UNUSABLE_PASSWORD,
                'date_joined': datetime.now()
                } )
        facebook_user.user = user
        facebook_user.save()

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except:
            return None