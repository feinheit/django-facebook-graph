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


function addTabToPage() {
    window.open("http://www.facebook.com/dialog/pagetab?app_id="
    +FACEBOOK_APP_ID+"&next="+FACEBOOK_REDIRECT_URL,
    "PageTab", "width=500,height=200");
}


window.fbAsyncInit = function() {
    FB._https = (window.location.protocol == "https:");
    FB.init({appId: FACEBOOK_APP_ID, status: true, cookie: true,
             xfbml: true, oauth: true,
             channelUrl : document.location.protocol + '//' + document.location.host + FACEBOOK_CHANNEL_URL }
    );

    canvas_resize();
    // Apparently this bug has been fixed.
    // FB.UIServer.setLoadedNode = function (a, b) { FB.UIServer._loadedNodes[a.id] = b; };
    FB.getLoginStatus(function(response) {
      log(response);
      fb['status'] = response.status;
      if (response.status === 'connected') {
        fb.authResponse = response.authResponse | response.auth ;
        fb.user = (function(){ return fb.authResponse; })(); // For backwards compatibility. Will be removed at some point.
        fb.user.warning = 'This property is deprecated and will be removed! Use fb.auth instead.';
      }
      FQ.run();
    }, 'json');
  };

FQ.add(function(){
    FB.Event.subscribe('auth.login', function(response){
        if (fb.status != 'connected') {
            /*
            var url = window.location.toString();
            url.match(/\?(.+)$/);
            var params = RegExp.$1;
            */
            top.location.href = FACEBOOK_REDIRECT_URL ;
        }
    });
});

