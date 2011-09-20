/* add this to your base template:
    {% load fb_tags %}
    <script type="text/javascript">
        FACEBOOK_APP_ID = '{% fb_app_id feincms_page.facebook_application %}';
        FACEBOOK_REDIRECT_URL = '{% fb_redirect_url feincms_page.facebook_application %}';
        FACEBOOK_CHANNEL_URL = '{% url channel %}';
    </script>
    <script type="text/javascript" src="{{ STATIC_URL }}facebook/fb_utils.js"></script>
    
    
    add this to the bottom of your base.html:
    
    <div id="fb-root"></div>
    <script type="text/javascript">
    (function() {
	    var e = document.createElement('script'); e.async = true;
	    e.src = document.location.protocol +
	    '//connect.facebook.net/de_DE/all.js';
	    document.getElementById('fb-root').appendChild(e);
	}());
    </script>
    
    add     url(r'^facebook/', include('facebook.urls')), to yor urls.py. 
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
      if (response.status === 'connected') {
        fb.auth = response.authResponse;
        fb.user = (function(){ return fb.auth; })(); // For backwards compatibility. Will be removed at some point.
        fb.user.warning = 'This property is deprecated and will be removed! Use fb.auth instead.';
        fb['status'] = response.status;
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

