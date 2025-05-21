/*jshint esversion: 6*/

var host = window.location.protocol + "//" + window.location.host;

function perform_JWT_refresh(){
  console.log("JWT refresh starts");
  return $.ajax({
    method: 'POST',
    url: host + "/login/refresh",

    success: function(response) {
      console.log("JWT refresh success");
    },
    error: function(response){
      console.log("JWT refresh error");
      var status = response.status;
      if (status == 401) {
        //redirect to login page
        alert("Your session expired.");
        console.log("refresh 401: Unauthorized");
        window.location = "login.html";
      } else if (status == 403) {
        //redirect to login page
        alert("Refresh attempt with insufficient rights.");
        window.location = "login.html";
        console.log("refresh 403: Insufficient rights.")
      } else {
        console.log("refresh error: ", status, response.responseText);
      }
    },
  });
}


