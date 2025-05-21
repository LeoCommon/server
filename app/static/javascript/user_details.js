/*jshint esversion: 6*/
var sensors = []; // list of documents with sensor_id(int) and job strings(array)
var host = window.location.protocol + "//" + window.location.host;


// assigning functions to the left menu items
document.getElementById('logoutButton').onclick = logout;
//document.getElementById('ch_pwd_btn').onclick = notYetImplemented;
document.getElementById('ch_mail_btn').onclick = change_email;
document.getElementById('ch_role_btn').onclick = change_role;
document.getElementById('ch_rsa_btn').onclick = notYetImplemented;
document.getElementById('add_sensor_btn').onclick = notYetImplemented;
document.getElementById('rm_senor_btn').onclick = notYetImplemented;


// call the website with href redirection: Redirect the user: location.replace("http://example.com/Page_Two.html?" + data); location.replace("sensor_details.html?sensor_id=foo");

//Get the current link & remove all content before ?
link = window.location.href;
if (link.includes("user_details.html?user_id=")) {
  var user_id = link.split('user_details.html?user_id=').pop();
  document.getElementById("user_id").innerHTML = "ID: " + user_id;
  startCall();
} else {
  console.log("unknown user_id");
  // redirect to the user_list.html
  window.location = "user_list.html";
}


function startCall() {
  var user_id = link.split('user_details.html?user_id=').pop();
  $.ajax({
    dataTypr: 'json',
    method: 'GET',
    url: host + "/usermanagement/get_user_details/" + user_id,

    success: function(response) {
      user = response.data;
      //console.log(user);
      buildContent(user)
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(startCall);
      } else if (status == 403) {
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
        window.location = "user_list.html";
      } else {
        console.log("user-details-autoload error: ", status, response.responseText);
      }
    },
  });
}


function buildContent(user) {
  var name = user.username;
  document.getElementById("user_name_field").innerHTML = name;
  var id = user.id;
  document.getElementById("user_id").innerHTML = "ID: " + id;
  var email = user.email;
  document.getElementById("user_mail").innerHTML = "email: " + email;
  var role = user.role;
  document.getElementById("user_role").innerHTML = "role: " + role;
  var rsa = user.public_rsa_key;
  document.getElementById("user_rsa").innerHTML = "public RSA key: " + rsa;
  var sensorstring = user.owned_sensors;
  document.getElementById("user_sensors").innerHTML = "owned sensors: " + sensorstring;
  var jobstring = user.scheduled_jobs;
  document.getElementById("user_jobs").innerHTML = "scheduled Jobs: " + jobstring;
  var creation_string = timestamp_2_timestring(user.creation_date);
  document.getElementById("user_creation").innerHTML = "account creation time: " + creation_string[0];
  var online_status = user.online_status
  var online_string = timestamp_2_timestring(online_status[0][1]);
  if (online_string[2] < 6*60) {
    online_string_add = " (online)"
  } else {
    online_string_add = " (offline since " + online_string[1] +")"
  }
  document.getElementById("user_online").innerHTML = "last online: " + online_string[0] + online_string_add;
}


function timestamp_2_timestring(utc_timestamp) {
  var date_obj = new Date(utc_timestamp * 1000);  // requires ms
  var hours = '0' + date_obj.getUTCHours();
  var minutes = '0' + date_obj.getUTCMinutes();
  var seconds= '0' + date_obj.getUTCSeconds();
  var my_time = Math.floor(Date.now() / 1000);
  // also calculate the diff to now
  var diff_time = my_time - utc_timestamp;
  var diff_sec = '0' + (diff_time % 60);
  var diff_min = '0' + (Math.trunc(diff_time / 60) % 60);
  var diff_hour = '' + Math.trunc(diff_time / 3600);
  if (diff_hour.length < 2) {
    diff_hour = '0' + diff_hour;
  }
  var time_string = date_obj.getUTCDate() + '-' + (date_obj.getUTCMonth()+1) + '-' + date_obj.getUTCFullYear() + ', ' + hours.substr(-2) + ':' + minutes.substr(-2) + ':' + seconds.substr(-2) + ' (UTC)';
  var diff_string = diff_hour + ':' + diff_min.substr(-2) + ':' + diff_sec.substr(-2);
  return [time_string, diff_string, diff_time]
}

function change_email(){
  var new_email = prompt("Enter the new email:")
  if(new_email == null) {return;} // cancel when user doesn't confirm
  var user_id = link.split('user_details.html?user_id=').pop();

  $.ajax({
    dataTypr: 'json',
    method: 'PUT',
    url: host + "/usermanagement/change_user_email/" + user_id + "?new_email=" + new_email,

    success: function(response) {
      console.log("email changed.");
      window.location.reload();
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(change_email);
      } else if (status == 403) {
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
        window.location = "user_list.html";
      } else {
        console.log("user change email error: ", status, response.responseText);
      }
    },
  });
}

function change_role(){
  //adding the possiblel user roles to the role dropdown
  
  $.ajax({
    dataTypr: 'json',
    method: 'GET',
    url: host + "/usermanagement/get_role_list",

    success: function(response) {
      var new_role = prompt("\nPossible roles: "+response.data+"\n\nEnter the new role:");
      if(new_role == null) {return;} // cancel when user doesn't confirm
      var user_id = link.split('user_details.html?user_id=').pop();

      $.ajax({
        dataTypr: 'json',
        method: 'PUT',
        url: host + "/usermanagement/change_user_role/" + user_id + "?new_role=" + new_role,
    
        success: function(response) {
          console.log("role changed.");
          window.location.reload();
        },
        error: function(response){
          var status = response.status;
          if (status == 401) {
            console.log("401: Unauthorized")
            perform_JWT_refresh().done(change_email);
          } else if (status == 403) {
            alert("Insufficient rights.");
            console.log("403: Insufficient rights.")
            window.location = "user_list.html";
          } else {
            alert("Error. Check if correct role was entered and try again.");
            console.log("user role change error: ", status, response.responseText);
          }
        },
      });

    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(startCall);
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else {
        console.log("user-role-list autoload error: ", status, response.responseText);
      }
    },
  });
}


function notYetImplemented(){
  console.log("button not yet implemented");
  alert('Button not yet implemented!');
}





// handle the 'add new user' dialog (from: https://jqueryui.com/dialog/#modal-form)
$( function() {
  var dialog, form,

    // From http://www.whatwg.org/specs/web-apps/current-work/multipage/states-of-the-type-attribute.html#e-mail-state-%28type=email%29
    enter_password = $( "#password1" ),
    confirm_password = $( "#password2" ),
    allFields = $( [] ).add( enter_password ).add( confirm_password ),
    tips = $( ".validateTips" );

  function updateTips( t ) {
    tips
      .text( t )
      .addClass( "ui-state-highlight" );
    setTimeout(function() {
      tips.removeClass( "ui-state-highlight", 1500 );
    }, 500 );
  }
  
  function checkLength( o, n, min, max ) {
    if ( o.val().length > max || o.val().length < min ) {
      o.addClass( "ui-state-error" );
      updateTips( "Length of " + n + " must be between " + min + " and " + max + "." );
      return false;
    } else {
      return true;
    }
  }

  function changePW() {
    var valid = true;
    allFields.removeClass( "ui-state-error" );
    var user_id = link.split('user_details.html?user_id=').pop();

    valid = valid && checkLength( enter_password, "password", 6, 64 );
    valid = valid && checkLength( confirm_password, "password", 6, 64 );
    if ( confirm_password.val() != enter_password.val() ) {
      updateTips("Passwords to not match!")
      return;
    }
   
    if ( valid ) {

      pre_data = '{"password":'+'"'+enter_password.val()+'"}'

      $.ajax({
        method: 'PUT',
        dataTypr: 'json',
        contentType: "application/json",
        url: host + "/usermanagement/change_user_password/" + user_id,
        data: pre_data,

        success: function(response) {
          console.log("user PW changed");
          dialog.dialog( "close" );
          alert("Password sucessfully changed.");
        },
        error: function(response){
          var status = response.status;
          if (status == 401) {
            //redirect to login page
            console.log("401: Unauthorized")
            perform_JWT_refresh().done(changePW);
          } else if (status == 403) {
            //redirect to login page
            alert("Insufficient rights.");
            console.log("403: Insufficient rights.")
          } else {
            console.log("change-user-pw error: ", status, response.responseText);
          }
        },
      });
      // dialog.dialog( "close" );
    }
    return valid;
  }

  dialog = $( "#change_password_dialog" ).dialog({
    autoOpen: false,
    height: 500,
    width: 400,
    modal: true,
    buttons: {
      "change Password": changePW,
      Cancel: function() {
        dialog.dialog( "close" );
      }
    },
    close: function() {
      form[ 0 ].reset();
      allFields.removeClass( "ui-state-error" );
    }
  });

  form = dialog.find( "form" ).on( "submit", function( event ) {
    event.preventDefault();
    changePW();
  });

  $( "#ch_pwd_btn" ).button().on( "click", function() {
    dialog.dialog( "open" );
  });
} );
