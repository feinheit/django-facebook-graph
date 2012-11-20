#coding=utf-8
""" Views for game-related task such as getting and settings scores and achievments. """

from facebook.modules.profile.user.models import User
from facebook.modules.profile.application.utils import get_app_dict
from .models import Score

from facebook.graph import get_static_graph

def get_user_score(user_id, graph):
    """If the user has granted your app with the user_games_activity permission then 
       this api will give you scores for all apps for that user. 
       Otherwise it will give you scores only for your app.
       The friends_games_activity permission will enable you to access scores 
       for users' friends for all apps
    """
    
    scores = graph.request('%s/scores' % user_id )
    return scores['data']


def get_user_and_friends_scores(user_id, graph, app_name=None):
    """This returns the list of scores for the user and their friends who have a uthorized the app.
       You can use this api to create leaderboard for the user and their friends.
       The graph must contain the user access_token!
    """
    application = get_app_dict(app_name)
    
    scores = graph.request('%s/scores' % application['ID'])
    
    return scores['data']  
        

def set_user_score(user_id, score, app_name=None, facebook=True):
    graph = get_static_graph(app_name=app_name)
    user_id = int(user_id)
    if int(score) < 0:
        raise AttributeError, 'Score < 0.'
    else:
        user, created = User.objects.get_or_create(id=user_id)
        if created:
            user.get_from_facebook(save=True, graph=graph)
    obj, created = Score.objects.get_or_create(_user_id=user_id, defaults={'_score':0})
    if not created and int(score) < obj._score:
        return 'score lower than current score. Not updated.'
    else:
        obj._score = int(score)
        obj._user = user
        response = obj.save(graph=graph)
        return response
    

def delete_user_score(user_id, app_name=None):
    """ This deletes the user's score for this app. """
    graph = get_static_graph(app_name=app_name)
    
    return graph.request('%s/scores' % user_id, post_args={'method': 'delete'})


def delete_all_scores(app_name=None):
    """ This deletes all scores for this app. """
    graph = get_static_graph(app_name=app_name)
    application = get_app_dict(app_name)
    
    return graph.request('%s/scores' % application['ID'], post_args={'method': 'delete'})