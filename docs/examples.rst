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


The problem here is that if there is no session, you won't get a signed request. 
So you have to force it.
Add the following code to your landing page. It checks if the login was successful::

    {% block extra-js %}
    <script type="text/javascript">
        FQ.add(function(){
            if(fb.status == 'connected')
            { 
               {% if not request.user.is_authenticated %}
                    {% if request.method == 'GET' %}
                        force_signed_request(fb);
                    {% else %}
                        window.location = '{% url fb_connect %}';
                    {% endif %}
               {% endif %}
            }
        });
    </script>
    {% endblock %}
    
    
