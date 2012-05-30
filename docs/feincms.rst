Using django-facebook-graph with FeinCMS
========================================

The facebook page extension allows you to have several Facebook apps assigned to
different FeinCMS pages. This way you can have multiple tabs on your Facebook page
and manage them in a single admin.


Facebook Application Extension
------------------------------

In your models.py add::

    from facebook.feincms.extensions import facebook_application

    Page.register_extension(facebook_application)


Make sure you have installed the fb.Page module
In the FeinCMS admin add your Facebook pages. The FeinCMS pages have two additional fields
for the facebook app and page. If the page is set, the content can only be displayed within
that page.
The app is used to decrypt the signed request.


Content Type Extension
----------------------

This is a monkey-patch for FeinCMS contents. It adds two fields: render_like and app_installed.
It allows to control if a content type is displayed whether a user has liked a page or not
or has installed the app.

Because it's a monkey-patch the order of import is important (models.py)::

    from feincms.content.richtext.models import RichTextContent
    from facebook.feincms.extensions import content_type_extension

    content_type_extension(RichTextContent)

