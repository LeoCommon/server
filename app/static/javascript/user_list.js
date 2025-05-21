/*jshint esversion: 6*/
var sensors = []; // list of documents with sensor_id(int) and job strings(array)
var host = window.location.protocol + "//" + window.location.host;

// assigning functions to the left menu items
document.getElementById('logoutButton').onclick = logout;

window.onload = startCall();

//when the window is loaded this function is triggered to either load the users and build the table or show insufficient rights
function startCall() {
  $.ajax({
    dataTypr: 'json',
    method: 'GET',
    url: host + "/usermanagement/get_user_list",

    success: function(response) {
      users = response.data;
      buildTable(users);
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
        console.log("users-autoload error: ", status, response.responseText);
      }
    },
  });

  
}


function buildTable(users) {
    var table = document.getElementById('user_table_content');

    for (var i = 0; i < users.length; i++) {
        var entry = users[i]; // one entry for each user
        var id = entry.id;
        var user_name = entry.username;
        var user_role = entry.role;
        var user_login_time = entry.online_status;
        user_login_time = user_login_time[0][1]
        var my_time = Math.floor(Date.now() / 1000)
        var diff_time = my_time - user_login_time;
        if (diff_time > 60*6) {
            var time_string = 'offline';
        } else {
            var time_string = 'online';
        }
        // style options have to be in javascript to apply when rows are added dynamically
        var href_line = `<a class="clickables" href="user_details.html?user_id=${entry.id}">${entry.username}</a>`;
        var row = `
      <tr id="row-${entry.id}">
        <td class="columns_with_ellipsis_overflow" style="padding:0 5px 0 5px">${href_line}</td>
        <td style="padding:0 5px 0 5px">${time_string}</td>
        <td style="padding:0 5px 0 5px">${user_role}</td>
      </tr> `;

        $(`#user_table_content`).append(row);
    }
}


// handle the 'add new user' dialog (from: https://jqueryui.com/dialog/#modal-form)
$( function() {
  var dialog, form,

    // From http://www.whatwg.org/specs/web-apps/current-work/multipage/states-of-the-type-attribute.html#e-mail-state-%28type=email%29
    emailRegex = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
    user_name = $( "#name" ),
    user_role = $( "#role" ),
    user_email = $( "#email" ),
    user_password = $( "#password" ),
    allFields = $( [] ).add( user_name ).add( user_role ).add( user_email ).add( user_password ),
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
 
  function checkRegexp( o, regexp, n ) {
    if ( !( regexp.test( o.val() ) ) ) {
      o.addClass( "ui-state-error" );
      updateTips( n );
      return false;
    } else {
      return true;
    }
  }


  function addUser() {
    var valid = true;
    allFields.removeClass( "ui-state-error" );

    valid = valid && checkLength( user_name, "username", 3, 25 );
    valid = valid && checkLength( user_email, "email", 6, 80 );
    valid = valid && checkLength( user_password, "password", 6, 64 );
 
    valid = valid && checkRegexp( user_name, /^([0-9a-z\-_.:\+()@])+$/i, "Unallowed character! Username may consist of a-z, 0-9, '-', '_', '.', ':', '+', '(', ')' , '@'." );
    valid = valid && checkRegexp( user_email, emailRegex, "Unallowed character! Email example: test@mail.com" );
 
    if ( valid ) {

      pre_data = '{"email": '+'"'+user_email.val()+'"'+
        ', "username": '+'"'+user_name.val()+'"'+
        ', "password":'+'"'+user_password.val()+'"'+
        ', "role":'+'"'+user_role.val()+'"}'

      $.ajax({
        method: 'POST',
        dataTypr: 'json',
        contentType: "application/json",
        url: host + "/usermanagement/register_user",
        data: pre_data,

        success: function(response) {
          console.log("added new user");
          location.reload();
        },
        error: function(response){
          var status = response.status;
          if (status == 401) {
            //redirect to login page
            console.log("401: Unauthorized")
            perform_JWT_refresh().done(addUser);
          } else if (status == 403) {
            //redirect to login page
            alert("Insufficient rights.");
            console.log("403: Insufficient rights.")
          } else {
            console.log("add-new-user error: ", status, response.responseText);
          }
        },
      });
      // dialog.dialog( "close" );
    }
    return valid;
  }

  dialog = $( "#add_user_dialog" ).dialog({
    autoOpen: false,
    height: 500,
    width: 400,
    modal: true,
    buttons: {
      "Add New User": addUser,
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
    addUser();
  });

  $( "#add_user" ).button().on( "click", function() { 
    //adding the possiblel user roles to the role dropdown
    $.ajax({
      dataTypr: 'json',
      method: 'GET',
      url: host + "/usermanagement/get_role_list",

      success: function(response) {
        roles = response.data;
        roles.forEach((elem) => document.getElementById("role").add(new Option(elem)));

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

    //open dialog
    dialog.dialog( "open" );
  });
} );

