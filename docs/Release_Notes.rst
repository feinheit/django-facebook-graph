===================================
Django-facebook-graph Release Notes
===================================

Due to the high update cycle there are no version numbers. The release notes are structured by
the date the change has been added to the repo.


June 22, 2012
=============

 * Move game views to game module
 * custom CSRF middleware is no longer necessary. Just put SignedRequestMiddleware in between SessionMiddleware
   and Django's csrfViewMiddleware.



May 19, 2012
============

 * Add field '_access_token_expires' to fb.Page model.
 * Add field 'created' to fb.Post model.
 * Add insight link to page
 * Working deauthorize callback with preview
 * docs update
