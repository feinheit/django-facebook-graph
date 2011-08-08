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

