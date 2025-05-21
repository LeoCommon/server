/*jshint esversion: 6*/
var host = window.location.protocol + "//" + window.location.host;

document.getElementById("loginButton").onclick = validate;
  
function validate(event){
  console.debug("Call User Login");
  var username = document.getElementById("username").value;
  var password = document.getElementById("password").value;
    
  pre_data = ' {"username":"'+username+'"'+', "password":"'+password+'"}';

  console.debug("Perform User Login:" + pre_data);
  console.debug("url:" + host + "/login/userlogin");

  //call server side function for user validation
  $.ajax({
    method: 'POST',
    contentType: "application/json",
    url: host + "/login/userlogin",
    data: pre_data,

    success: function(response){
      //redirect to home page
      event.preventDefault();
      console.log("Login successful");
      window.location = "data.html";
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        //redirect to login page
        console.log("401: Unauthorized")
        window.location = "login.html";
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else {
        console.log("deleteEntry error: ", status, response.responseText);
      }
    },
  });
  return false;  /* prevent reloading */
}


