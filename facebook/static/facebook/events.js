FQ.add(function(){
    if($.isEmptyObject(fb.user)){
        $('.fb-event-rsvp').hide();
        $('.fb-event-login').show();
    } else {
        $('.fb-event-rsvp').show();
        $('.fb-event-login').hide();  
    }
});
$(function(){
    /*
    function rsvp(session){
         $('.fb-event').each(function(){
            if($.inArray($(this).data('id'), user_events) != -1){
                log($(this).data('id'));
            }
            
         });
    }    
    */

    function login(button){
        FB.login(function(response) {
          if (response.session) {
            if (response.perms) {
              fb.user = response.session;
              fb.perms = response.perms.split(',');
              log(fb.perms);
              button.trigger('click');
              // perms is a comma separated list of granted permissions
            } 
          } 
        }, {perms:'rsvp_event, user_events'});
    }
    $('.fb-event-rsvp button').click(function(evt){
       var event_id = $(this).parent('div').data('id');
       var button = $(this);
       var status = $(this).attr('rel');
       if(fb.user && $.inArray('rsvp_event', fb.perms)!= -1){
           $('.fb-button').removeClass('selected');
           FB.api('/'+ event_id + '/' + status, 'post', function(response) {
           if (!response || response.error) {
                alert('Error occured');
                log(response);
              } else {
                button.addClass('selected');
              }
           });
       } else {
           login(button);
       }

    });
 
});
