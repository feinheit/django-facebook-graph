================================================
A toolset to use facebooks graph api with django
================================================

Features
========

 * Django wrapper for the Facebook Graph and FQL API.
 * Fully supports Oauth 2
 * simple access to Facebook data. As in graph.request(user_id).
 * Django auth backend for Facebook connect.
 * Upload Photo and Videos to a user's account.
 * Facebook models are cached locally.
 * The signed request is automatically stored in the session.
 * Multiple Facebook apps are possible for each Django project. 
 * Uses the OAuth 2.0 authentification.


Read the documentation on:
http://readthedocs.org/docs/django-facebook-graph/en/latest/

This version works with OAuth 2.0 only!

Note
====

There is a new version in the works. You can check it out in the `structured` branch.
Most of the new development is done there. Once it is ready this branch will be renamed to `legacy`.


Graph helper tools:
==============================

 * add 'facebook' to your INSTALLED_APPS. This will create django classes for the main facebook models.
 * add 'SignedRequestMiddleware' to your settings.MIDDLEWARE.
 * optionally add 'AppRequestMiddleware' if you need to deal with app requests.
 * add url(r'^facebook/', include('facebook.urls')), to your urls.py.
 * create an app settings dict as described in utils.py for each of your apps. I recommend using a different settings file for local development.
 * for client side utilities add fb_utils to your html template and follow the instructions in the comments section.

Now you can generate a graph instance with the following command::

    from facebook.utils import get_graph    
    graph = get_graph(request)
    
To make a graph request to facebook simply use graph.request. I.e. to get a certain message object::

    fb_message = graph.request('%s' % post_id)

You can also create facebook user objects like so::

    from facebook.models import User
    user = User(id=graph.me['id'])
    user.get_from_facebook(graph=graph, save=True)

The app stores as much data as possible in the session to minimize requests to Facebook. You can access the session class directly 
to get informations about the current user::
  
    fb = request.fb_session
    signed_request = fb.signed_request



Facebook Models
===============

The facebook app adds the models: Users, Events, Pages, Photos, Posts and Requests to the admin interface. Django can fetch the
data from facebook on save and store it locally. It is not yet possible to create a model this way and upload it to facebook except for Photos.
There is a login button so you can access private data as well. 



Simple usage of Facebook Auth:
==============================

 * add 'facebook' to your INSTALLED_APPS. it will create a table where to store all connected facebook users.
 * add 'facebook.backends.authentication.AuthenticationBackend' to AUTHENTICATION_BACKENDS
 * add url(r'^accounts/', include('facebook.backends.registration.urls')) to your urls
 * now you can insert the facebook button: <fb:login-button perms="email" onlogin="window.location.href='{% url auth_login %}?next={{ request.get_full_path }}'"></fb:login-button> 


Client side utilities:
======================

 * FQ Facebook queue that gets executed when the user login status is clear. Use FQ.add(function(){...});
 * fb object that contains the user details and permissions.
 * async init method with channel URL. Some fixes for IE.
 * a log function that can record client side responses back to the server.


Test Users:
===========

Facebook allows you to have an army of test users to test your apps. 
While DEBUG is True, you can see the testuser model in the admin frontend.
To create a testuser for your app use the following command::
    
    ./manage.py create_testuser -i

To show a list of registered testusers attached to your app type::

    ./manage.py testusers

This will give you a list with the names and login-URLs of the testusers. A star in front of the
name means the testuser has installed your app.

To friend testusers you can use the following command::

    ./manage.py friend <TESTUSER-id> [<TESTUSER-2-id>]

If TESTUSER-2-id is not specified, the app will try to friend every testuser.
Testusers must have the app installt to allow friend relationships through this command.

There is also a fb_testuser_menu template tag. The tag adds a select menu that allows you to select
a testuser. You are then redirected to the facebook page of that test user (and logged in).
The tag has to fetch the login-url for every testuser associated to the app and might be a bit slow
when you have a lot of test users installed. I suggest putting the tag in the admin template.


Template Tags:
==============

{% fb_app_settings %} Adds a (X) button that links to the Facebook page where you can deauthorize 
your app.
{% query_page_fan %} returns True if the user is fan of the page where the app tab is in.
{% fb_app_id [app_name] %} Returns the app id. Similiar tags for canvas page, canvas_url, redirect url and domain. 
