/* Please go to the following URL for installation instructions:

http://readthedocs.org/docs/django-facebook-graph/en/latest/installation.html
*/

/* This is due to a bug in IE8 */
function canvas_resize() {
    if (window.location.search.toString().indexOf('fb_xd_fragment') == -1) {
        FB.Canvas.setSize();
    }
}

FQ = {
    queue: new Array(),
    add: function(f) { if (typeof f == 'function') { this.queue.push(f); } },
    run: function() { while(this.queue.length > 0) { f = this.queue.pop(); f();
                      canvas_resize(); } }
};
var fb = {
    user: {}, // DEPRECATED Property. Here for backwards compatibility.
    get_perms : function(callback) {
                    var _perms = false;
                    return (function() {
                        if (_perms) {
                            callback(_perms);
                            return true;
                        }
                        _perms = [];
                        FB.api('/me/permissions/', function(data){
                            for (var i in data['data'][0]) {_perms.push(i);}
                            callback(_perms);
                            return true;
                        });
                    })()
                }
    };



window.fbAsyncInit = function() {
    FB.init({appId: FACEBOOK_APP_ID, status: true, cookie: true,
             xfbml: true, oauth: true,
             channelUrl : document.location.protocol + '//' + document.location.host + FACEBOOK_CHANNEL_URL }
    );
    canvas_resize();
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

FQ.add(function(){
    FB.Event.subscribe('auth.login', function(response){
        if (fb.status != 'connected') {
            var url = window.location.toString();
            url.match(/\?(.+)$/);
            var params = RegExp.$1;
            top.location.href = FACEBOOK_REDIRECT_URL ;
        }
    });
});

function log_error(url, message, csrf_token) {
    $.post( url,
        {'csrfmiddlewaretoken': csrf_token,
         'message': message },
         function(response){
             log(response);
         }, 'text'
    );
}
function post_to_url(path, params, method) {
    method = method || "post"; // Set method to post by default, if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        var hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", params[key]);

        form.appendChild(hiddenField);
    }

    document.body.appendChild(form);
    form.submit();
}

// Use this function for facebook connect if the user is connected to facebook
// but not to Django. This will send the signed request. After this, redirect to auth/connect.

function force_signed_request(fb) {
    if (fb.status != 'connected') { return false; }
    params = { 'signed_request' : fb.authResponse.signedRequest }
    post_to_url(window.location.toString(), params);
}

