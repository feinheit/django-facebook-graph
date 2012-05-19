/* Please go to the following URL for installation instructions:

http://readthedocs.org/docs/django-facebook-graph/en/latest/installation.html
*/

if (typeof(window.log) == 'undefined') {
    window.log = function(){
      log.history = log.history || [];   // store logs to an array for reference
      log.history.push(arguments);
      if(this.console){
        console.log( Array.prototype.slice.call(arguments) );
      }
    };
}

/* This is due to a bug in IE8 */
function canvas_resize() {
    if (window.location.search.toString().indexOf('fb_xd_fragment') == -1) {
        FB.Canvas.setSize();
    }
}

FQ = {
    queue: new Array(),
    add: function(f) { if (typeof f == 'function') { this.queue.push(f); } },
    run: function() { while(this.queue.length > 0) { f = this.queue.pop(); f(); }
                      canvas_resize();
                     }
};
var fb = {
    user: {}, // DEPRECATED Property. Here for backwards compatibility.
    get_perms : function(callback) {
                    fb._perms = fb._perms || false;
                    return (function() {
                        if (fb._perms) {
                            if(callback) {callback(fb._perms)};
                            return fb._perms;
                        }
                        fb._perms = [];
                        FB.api('/me/permissions/', function(data){
                            for (var i in data['data'][0]) {fb._perms.push(i);}
                            if(callback) {callback(fb._perms);}
                            return true;
                        });
                    })();
                }
    };


window.fbAsyncInit = function() {
    FB.init({appId: FACEBOOK_APP_ID, status: true, cookie: true,
             xfbml: true, oauth: true }
    );
    canvas_resize();
    // Apparently this has been fixed.

    FB.getLoginStatus(function(response) {
      log(response);
      fb['status'] = response.status;
      if (response.status === 'connected') {
        fb.authResponse = response.authResponse;
        fb.user = (function(){ return fb.authResponse; })(); // For backwards compatibility. Will be removed at some point.
        fb.user.warning = 'This property is deprecated and will be removed! Use fb.auth instead.';
      }
      FQ.run();
    }, 'json');
  };

