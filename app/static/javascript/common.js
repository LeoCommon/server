//javascript that is used on all pages and should be in one global place

//logout
function logout(event){
    $.ajax({
      method: 'DELETE',
      url: host + "/login/logout",
  
      success: function(response){
        //redirect to login page
        event.preventDefault();
        console.log("Logout successful");
        window.location = "login.html";
      },
      error: function(response){
        var status = response.status;
        if (status == 401) {
            console.log("401: Unauthorized")
            perform_JWT_refresh().done(function() {logout(event)});
        } else if (status == 403) {
          //redirect to login page
          alert("Insufficient rights.");
          console.log("403: Insufficient rights.")
        } else {
          console.log("logout error: ", status, response.responseText);
        }
      },
    });
  }