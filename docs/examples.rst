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


Fetch a user's newsfeed
-----------------------

This one is tricky due to Facebook's new privacy policy.
You could might want to use::

    graph.request('me/feed')

Unfortunately this returns only your own posts as well as friend's posts that have
been marked as public. Posts from friends that have been marked as 'Friends only' won't show up.
But you can use::

    graph.request('me/home')

This returns the last 25 posts from the user's wall. Unfortunately this does not really work
with test users.


Deeplinks into Facebook Tabs
----------------------------

Getting a static URL that is shareable on Facebook of a page within a Tab is tricky.
The only way to do deeplinking is to add the path as app_data parameter to the URL and then parse it.
Unfortunately a URL like this will not be accessible by the Facebook linter since it cuts off all GET 
parameters of facebook URLs.

A workaround for this is using the canvas URL and top-redirecting into the tab using the path as 
app_data parameter.

That's where the redirect_to_page decorator comes in. Decorate your index view and every view that might
get called directly and it checks if the page is correctly embedded within a Facebook page.
If it's not it will redirect the user into the tab.

The decorator needs a new value in the app_dict. A list of allowed Facebook Page IDs for the tab:
PAGES=[<page_id>,...]. The decorator needs to be called with the app name as parameter::

    from facebook.decorators import redirect_to_page

    @redirect_to_page('myapp')
    def index(request):
        more code here.
        

Page Login
==========

To allow an app to post to a Facebook Page, a page administrator needs to grant the app the
manage_pages permission.
If you have multiple apps, you have to define the following in settings.py::

    DEFAULT_POST_APP = 'myapp'

You need to have a Facebook login button on the Page admin template and make sure you are
logged in.
Then select the pages you want to have the app access to and choose 'Get an access token for
the selected page(s)' from the admin actions. If everything worked out, you should have a
checkmark on the right. From now on your app can do the same things you can do.

Keep in mind that new access token expire after 60 days.
