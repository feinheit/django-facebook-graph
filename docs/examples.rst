Use Cases for django-facebook-graph
===================================


Facebook Connect with Django
----------------------------

You can automatically login a user that has already been authenticated. Add
this to your ``login.html`` template::

    {% block extra-js %}
    {% if not request.user.is_authenticated %}
    <script type="text/javascript">
    FQ.add(function(){
        if(fb.status == 'connected') {
            window.location = '{% url fb_connect %}?next={% url myview %}';
        }
    });
    </script>
    {% endif %}
    {% endblock %}


For views that require a logged in user you could either check the status on
the server with ``graph.me``, or better, on the client side with the following
piece of code::

    {% if request.user.is_authenticated %}
    FQ.add(function(){
        if (fb.status == 'not_authorized') {
            window.location = '{% url fb_logout %}';
        }
    });
    {% endif %}

The advantage of checking the status in the browser is that the response time
is usually shorter.


App Tabs and Facebook login
---------------------------

It is not easy to do a deeplink into an app tab. Facebook doesn't really support it.
The only workaround is using the `Redirect2AppDataMiddleware` and calling facebook/redirect
with the url urlencoded as app_data parameter.

That's how it looks::

    'REDIRECT-URL': 'http://apps.facebook.com/<MY_APP_NAMESPACE>/facebook/redirect/?next=http%3A%2F%2Fwww.facebook.com%2F<FB_PAGE>%3Fsk%3Dapp_<APP_ID>%26app_data%3D%2<DEEPLINK_URL>%2F',
    
Make sure you have the `canvas url` parameters in the developer app set to the root
or wherever facebook should fetch the redirect from.


Login while keeping the App requests
------------------------------------

On some browsers you have to make sure that all protocols match. I.e. if your iframe is loaded 
via https you cannot redirect to a http url. The problem here is that if Facebook itself is on a 
http url the redirect will be to the http url as well.
::
    <fb:login-button scope="email" onlogin="login_redirect();"></fb:login-button>
    
    function login_redirect(){
        window.location = ('https:' == location.protocol ? 'https://' : 'http://')+'yourdomain.com{% url join_team %}{% if request.GET.request_ids %}?request_ids={{ request.GET.request_ids }}{% endif %}';
    }
    





