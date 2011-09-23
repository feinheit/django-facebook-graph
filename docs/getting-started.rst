.. _getting-started:

==========================================
Getting started with django-facebook-graph
==========================================


You need to create a Facebook Application on Facebook Developers for nearly
every functionality of ``django-facebook-graph``.

    https://developers.facebook.com/apps

For detailed installation istructions check out the :ref:`installation` section.


Facebook Connect support for your website
=========================================

Currently the framework supports user login with the facebook login button. It's fairly plug and play.
Make sure you have added the auth.backend and login url as described in the :ref:`installation` instructions.

Adding the Facebook login to your website
-----------------------------------------

FBML tags::

    <fb:login-button scope="email" onlogin="window.location.href='{% url auth_login %}?next=/'"></fb:login-button>

Checkout the facebook documentation on the login button: 
http://developers.facebook.com/docs/reference/plugins/login/


Using the graph API
===================

You can generate a graph instance with the following command::

    from facebook.utils import get_graph    
    graph = get_graph(request)
    
To make a graph request to facebook, simply use graph.request(). I.e. to get a certain message object::

    fb_message = graph.request('%s' % post_id)

You can also create facebook user objects like so::

    from facebook.models import User
    user = User(id=graph.me['id'])
    user.get_from_facebook(graph=graph, save=True)

The app stores as much data as possible in the session to minimize requests to Facebook. You can access the session class directly 
to get informations about the current user::
  
    from facebook.utils import get_session
    fb = get_session()
    signed_request = fb.signed_request


About the Access Token
----------------------
Facebook distinguishes between the app access token and the user access token. A user access token is needed for requests that need a user's
permission. It's generally more powerfull thann an app access token. You should generally get the user access token when you pass the request
argument to the get_graph(request=request) function.

However, some operations require the app access token. Like deleting app requests or saving user score. You can implicitly get the app access 
token by just calling graph=get_graph() without providing the request object, or explicitly by calling get_static_graph().


Sending posts onto a Facebook wall
==================================

Ensure your app has sufficient permissions
------------------------------------------

This snippet can be used to ask for the ``publish_stream`` extended
permission::

    function get_publish_perms(callback_fn) {
        FB.login(function(response) {
            if (response.session) {
                if (response.perms) {
                    // fb.perms.push(response.perms);
                    if (response.perms.indexOf('publish_stream') != -1) {
                        callback_fn();
                    }
                } else {
                    alert('No permission.');
                }
            } else {
                // user is not logged in
            }
        }, {perms:'publish_stream'});
    }

To determine whether a permission is already provided you culd use the following
snippet::

    FB.getLoginStatus(function(response) {
        fb.loginStatus = response;
        fb.perms = $.parseJSON(response.perms).extended;
    }, true);

The second parameter, ``true`` causes a reload of the login status. This
adds the permissions to the response too, which is very helpful for us.

the perms are also loaded into the fb object on page load. So you could also just try::
    
    if (fb.perms.indexOf('publish_stream') != -1) {
        post_to_wall();
    } else {
        FB.login(function(response){
                 }, 
                 {perms: 'publish_stream' }
        );      
    }

The logical consequence if the if-statement fails would be to make a call to FB.login() to show a login window. The problem here is
that most browsers block the popup if it doesn't follow an immediate user action. I therefore recommend to attach the above function to 
a click event on a button.


Actually create a Facebook wall post
------------------------------------

Now that everything else is taken care of actually creating the wall
post is easy::

    from facebook.utils import get_graph
    def my_view(request, ...):
        graph = get_graph(request)
        graph.put_wall_post('Hello World!', {
            'name': 'Link name',
            'link': 'http://www.example.com/at/this/location/',
            })

It might still be a good idea to enclose the ``put_wall_post`` call in
``try..except`` clause.

Keep in mind that if too many users remove a wallpost that had been created through the Graph API, 
your app will get classified as spam.



