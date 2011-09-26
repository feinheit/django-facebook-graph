Use Cases for django-facebook-graph
===================================



Facebook Connect with Django
----------------------------

You can automatically login a user that has already been authenticated. Add this to your
login.html template::

    {% block extra-js %}
    {% if not request.user.is_authenticated %}
    <script type="text/javascript">
    FQ.add(function(){
        if(fb.status == 'connected')
        {
           window.location = '{% url fb_connect %}?next={% url myview %}';
                }
        });
    </script>
    {% endif %}
    {% endblock %}


For views that require a logged in user you could either check the status on the server with `graph.me`, or better, on the client side with
the following piece of code::
    {% if request.user.is_authenticated %}
    FQ.add(function(){  
        if (fb.status == 'not_authorized'){
            window.location = "{% url fb_logout %}";
        }
    });
    {% endif %}
    
The advantage of checking the status in the browser is that the response time is usually shorter.
    
