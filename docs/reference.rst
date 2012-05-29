===============================
Django-facebook-graph reference
===============================

.. toctree::
   :maxdepth: 2

   installation
   clientside


Deauthorization callback
------------------------

There is a default url that can be called for the deauthorization callback::

    http://<canvas url>/facebook/deauthorize/<app name>/

The app name parameter is optional but needed if you have multiple apps to
decrypt the signed request. The default action is to delete the user model and
all related entries.


Testing the deauthorization callback
------------------------------------

If you are logged in to django you can test the deauthorization callback by calling this url::

    http://localhost.local:8000/facebook/deauthorize/<app name>/?userid=<user_id>

You will be shown a page like the one in the django admin
that shows you which entries would be deleted on a deauthorization callback.