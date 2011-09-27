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

