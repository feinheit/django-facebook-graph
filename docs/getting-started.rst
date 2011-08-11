.. _getting-started:

==========================================
Getting started with django-facebook-graph
==========================================


You need to create a Facebook Application on Facebook Developers for nearly
every functionality of ``django-facebook-graph``.

* https://developers.facebook.com/apps


Facebook Connect support for your website
=========================================

The Facebook Connect support consists of two parts: A backend for
django-registration_ which creates users and an authentication
backend which is responsible for the actual login on a Django website.

.. _django-registration: https://bitbucket.org/ubernostrum/django-registration


Setting the authentication backend
----------------------------------

We want to handle logins with the default backend first and fall back to
the Facebook authentication backend if the default backend couldn't handle
the login request::

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'facebook.backends.authentication.AuthenticationBackend',
    )


Activating the registration backend
-----------------------------------

The registration backend is set in ``urls.py`` (like all other registration
backends)::

    url(r'^accounts/', include('facebook.backends.registration.urls')),


Adding the Facebook login to your website
-----------------------------------------

``base.html``::

    window.fbAsyncInit = function() {
    FB.init({appId: '???????????????????', status: true, cookie: true,
             xfbml: true});
    };
    (function() {
    var e = document.createElement('script'); e.async = true;
    e.src = document.location.protocol +
      '//connect.facebook.net/en_US/all.js';
    document.getElementById('fb-root').appendChild(e);
    }());


FBML tags::

    <fb:login-button perms="email" onlogin="window.location.href='{% url auth_login %}?next=/'"></fb:login-button>



Sending posts onto a Facebook wall
==================================

Django configuration
--------------------

::

    MIDDLEWARE_CLASSES = (
        # ...
        'facebook.middleware.SignedRequestMiddleware',
        # ....

::

    window.fbAsyncInit = function() {
        FB.init({appId: '192738540778417', status: true, cookie: true,
                 xfbml: true});
    };
    (function() {
        var e = document.createElement('script'); e.async = true;
        e.src = document.location.protocol +
          '//connect.facebook.net/en_US/all.js';
        document.getElementById('fb-root').appendChild(e);
    }());


Ensure your app has sufficient permissions
------------------------------------------

This snippet can be used to ask for the ``publish_stream`` extended
permission::

    function get_publish_perms(callback_fn) {
        FB.login(function(response) {
            window.fb_response = response;
            if (response.session) {
                if (response.perms) {
                    //fb.perms.push(response.perms);
                    if (response.perms.indexOf('publish_stream') != -1) {
                        callback_fn();
                    }
                } else {
                    alert('Dann halt nicht.');
                }
            } else {
                // user is not logged in
            }
        }, {perms:'publish_stream'});
    }

To determine whether a permission is already provided use the following
snippet::

    var fb = {};
    FB.getLoginStatus(function(response) {
        fb.loginStatus = response;
        fb.perms = $.parseJSON(response.perms).extended;
    }, true);

The second parameter, ``true`` causes a reload of the login status. This
adds the permissions to the response too, which is very helpful for us.


Actually create a Facebook wall post
------------------------------------

Now that everything else is taken care of actually creating the wall
post is easy::

    from facebook.utils import get_graph
    def my_view(request, ...):
        graph = get_graph(request)
        graph.put_wall_post('Whatever', {
            'name': 'Some object',
            'link': 'http://www.example.com/at/this/location/',
            })

It might still be a good idea to enclose the ``put_wall_post`` call in
``try..except`` clause.
