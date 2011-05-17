/* add this to your base template:
    {% load fb_tags %}
    <script type="text/javascript">
        FACEBOOK_APP_ID = '{% facebook_app_id %}'
        FACEBOOK_REDIRECT_URL = '{% facebook_redirect_url %}'
    </script>
    <script type="text/javascript" src="{{ STATIC_URL }}facebook/fb_utils.js"></script>
 */

FQ = {
    queue: new Array(),
    add: function(f) { if (typeof f == 'function') { this.queue.push(f); } },
    run: function() { while(this.queue.length > 0) { f = this.queue.pop(); f();
                      FB.Canvas.setSize(); } }
};
var fb = {};
fb['user'] = {}
fb['perms'] = [];

  window.fbAsyncInit = function() {
    FB.init({appId: FACEBOOK_APP_ID, status: true, cookie: true,
             xfbml: true});
    FB.Canvas.setSize();
    FB.getLoginStatus(function(response) {
      log(response);
      if (response.session) {
        fb.user = response.session;
        if (response.perms){
            var perms = $.parseJSON(response.perms);
            fb.perms = perms.extended;
        } else {
            FB.api('/me/permissions/', function(data){
                for (var i in data['data'][0]) {fb.perms.push(i);}
            });
        }
      }
      FQ.run(); 
    }, 'json');
  };
(function() {
    var e = document.createElement('script'); e.async = true;
    e.src = document.location.protocol +
    '//connect.facebook.net/en_US/all.js';
    document.getElementById('fb-root').appendChild(e);
}());
  
$(function(){
    $('#invite').click(function(event) {
        $target = $(event.target);
        
        if (!$target.hasClass('loading')) {
            FB.ui({method: 'apprequests', 
                message: $('#invitation-text').val(), 
                data: $target.data('data')}, 
            function(response){
                $target.addClass('loading');
                $.post($target.data('target'), response, function(data) {
                    document.location.reload();
                });
            });
        }
    });
    
    $('.reminder-wallpost').click(function(event){
        $target = $(event.target);
         FB.ui(
           {
             method: 'feed',
             link: $target.data('url'),
             caption: $target.data('caption'),
             to: $target.data('to'),
             message: $('#invitation-text').val()
           },
           function(response) {
             if (response && response.post_id) {
               // alert('Post was published.');
             } else {
               // alert('Post was not published.');
             }
           }
         );
    });
    
    $('.attend').click(function(event){
        $target = $(event.target);
        document.location.href=$target.data('target')
    });
    
    FQ.add(function(){
        FB.Event.subscribe('auth.login', function(response){
            if ($.isEmptyObject(fb.user)) {
                var url = window.location.toString();
                url.match(/\?(.+)$/);
                var params = RegExp.$1;
                top.location.href = FACEBOOK_REDIRECT_URL ;
            }
        });
        FB.Event.subscribe('edge.create', function(response){
            log(response);
        });
    });
});