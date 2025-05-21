/*jshint esversion: 6*/
var sensors = []; // list of documents with sensor_id(int) and job strings(array)
var host = window.location.protocol + "//" + window.location.host;

// assigning functions to the left menu items
document.getElementById("add_jobs_to_all").onclick = addJobsToAll;
document.getElementById("clear_all_jobs").onclick = clearAllSensors;
document.getElementById("add_sensor").onclick = addSensor;
document.getElementById("remove_sensor").onclick = removeSensor;
document.getElementById('logoutButton').onclick = logout;
document.getElementById('update_location_list').onclick = update_location_list;

window.onload = startCall();

function startCall() {
  $.ajax({
    dataTypr: 'json',
    method: 'GET',
    url: host + "/sensors/",

    success: function(response) {
      sensors = response.data;
      buildTable(sensors);
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
        console.log("sensors-autoload error: ", status, response.responseText);
      }
    },
  });
}


function buildTable(sensors) {
    var table = document.getElementById('table_content');

    for (var i = 0; i < sensors.length; i++) {
        var entry = sensors[i]; // one entry for each sensor
        var id = entry.id;
        var jobstring = toJoblist(entry.jobs);
        var sensor_time = entry.status.status_time;
        var sensor_date = new Date(sensor_time * 1000);
        var sensor_hours = '0' + sensor_date.getUTCHours()
        var sensor_minutes = '0' + sensor_date.getUTCMinutes()
        var sensor_seconds= '0' + sensor_date.getUTCSeconds()
        var my_time = Math.floor(Date.now() / 1000)
        var diff_time = my_time - sensor_time;
        var diff_sec = '0' + (diff_time % 60)
        var diff_min = '0' + (Math.trunc(diff_time / 60) % 60)
        var diff_hour = '' + Math.trunc(diff_time / 3600)
        if (diff_hour.length < 2) {
          diff_hour = '0' + diff_hour;
        }
        var time_string = sensor_date.getUTCDate() + '-' + (sensor_date.getUTCMonth()+1) + '-' + sensor_date.getUTCFullYear() + ', ' + sensor_hours.substr(-2) + ':' + sensor_minutes.substr(-2) + ':' + sensor_seconds.substr(-2) + ' (UTC) (' + diff_hour + ':' + diff_min.substr(-2) + ':' + diff_sec.substr(-2) + ' ago)';
        // style options have to be in javascript to apply when rows are added dynamically
        var href_line = `<a class="clickables" href="sensor_details.html?sensor_id=${entry.id}">${entry.sensor_name}</a>`;
        var row = `
      <tr id="row-${entry.id}">
        <td class="columns_with_ellipsis_overflow" style="padding:0 5px 0 5px">${href_line}</td>
        <td style="padding:3px 5px 3px 5px">${time_string}</td>
        <td class="joblist columns_with_ellipsis_overflow" style="padding:0 5px 0 5px;word-wrap: break-word;">${entry.jobs}</td>
        <td class="buttonColumn" align="center" style="padding:0 5px 0 5px;">
            <button class="remove_btn small_buttons" type="button" id="clear-${entry.id}" data-sensor-name="${entry.sensor_name}" data-db-id="${entry.id}">
            Clear
            </button>
            <button class="small_buttons btn" type="button" id="add-${entry.id}" data-sensor-name="${entry.sensor_name}" data-db-id="${entry.id}">
            Add Job
            </button>
        </td>
      </tr> `;

        $(`#table_content`).append(row);
        $(`#clear-${entry.id}`).on('click', clearSensor);
        $(`#add-${entry.id}`).on('click', addJob);
    }
}

// turns joblist from database representation into table representation: ["job1", "job2"] -> job1,job2
function toJoblist(joblist_array) {
    var output = ""
    for (var i = 0; i < joblist_array.length; i++) {
        if (i < joblist_array.length - 1) { // append commata until last element
            output += joblist_array[i] + ","
        } else {
            output += joblist_array[i];
        }
    }
    return output;
}

function clearSensor() {
  // warning prompt
  let text = "clear job list of sensor "+$(this).data('sensorName')+"?";
  if (confirm(text) == true) {

    var db_id = $(this).data('dbId');
    var row = $(`#row-${db_id}`);
    var sensor_name = $(this).data('sensorName')
    console.log('{"sensor_name":' + '"'+sensor_name+'"'+',"jobs": []}');

    $.ajax({
      method: 'PUT',
      url: host + "/sensors/" + db_id,
      dataTypr: 'json',
      contentType: 'application/json',
      processData: false,
      data: '{"sensor_name":' + '"'+sensor_name+'"'+',"jobs": []}',

      success: function(response) {
        console.log("clear successful");
        $(`#row-${db_id} .joblist`).html("");
      },
      error: function(response){
        var status = response.status;
        if (status == 401) {
          console.log("401: Unauthorized")
          perform_JWT_refresh().done(clearSensor);
        } else if (status == 403) {
          //redirect to login page
          alert("Insufficient rights.");
          console.log("403: Insufficient rights.")
        } else {
          console.log("clearSensor error: ", status, response.responseText);
        }
      },
    });
  }
}

function addJob() {
  var db_id = $(this).data('dbId');
  var old_jobs = jQuery("#row-" + db_id + " .joblist").text(); // have: "job1,job2,job3" need: ["job1","job2","job3"]
  var new_job = prompt("Enter job: ");
  if (new_job === null){ //exit function if user chooses to cancel
    return;
  }

  // transform comma seperated string into array of strings
  // job1,job2,job3 -> ["job1","job2","job3"]
  // filter(Boolean) filters empty strings
  old_jobs_array = old_jobs.split(",").filter(Boolean);
  new_jobs_array = new_job.split(",").filter(Boolean);

  // concatenate new jobs from input with old joblist, allows multiple jobs to be added at once
  jobs_array = old_jobs_array.concat(new_jobs_array);
  console.log(jobs_array);

  $.ajax({
    method: 'PUT',
    contentType: 'application/json',
    url: host + "/sensors/" + db_id,
    data: '{"jobs": ' + JSON.stringify(jobs_array) + '}',

    success: function(response) {
      console.log("add job successful");
      // update table entry locally
      var jobs_string = toJoblist(jobs_array);
      $(`#row-${db_id} .joblist`).html(jobs_string)
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(addJob);
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else {
        alert("Error: Can't add the Job.\nCheck if the job exists and is still pending. Finished, failed or running jobs can't be added.\nOtherwise contact the team");
        console.log("adding Job error: ", status, response.responseText);
      }
    },
  });
}

function addJobsToAll() {
  var new_jobs = prompt("Enter jobs: ")
  if (new_jobs == null) {return;} // cancel when user chooses to cancel

  var new_jobs_array = new_jobs.split(",").filter(Boolean)

  $.ajax({
    method: 'PUT',
    contentType: 'application/json',
    url: host + "/sensors/all",
    data: '{"jobs": ' + JSON.stringify(new_jobs_array) + '}',

    success: function(response) {
      console.log("added jobs to all sensors");
      $('.joblist').each(function() {
        old_jobs = $(this).text().split(",").filter(Boolean);
        jobs_concat = old_jobs.concat(new_jobs_array);
        $(this).text(toJoblist(jobs_concat));
      });      
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(addJobsToAll);
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else {
        console.log("addJobsToAll error: ", status, response.responseText);
      }
    },
  });
}

function clearAllSensors() {
  let text = "Clear all job lists?";
  if (confirm(text) != true) {
    return;
  }

  $.ajax({
    method: 'POST',
    url: host + "/sensors/all",

    success: function(response) {
      console.log("cleared all sensor lists");
      $('.joblist').each(function() {
        $(this).text("");
      }); 
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(clearAllSensors);
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else {
        console.log("addJobsToAll error: ", status, response.responseText);
      }
    },
  });
}

function addSensor() {
  var new_sensor_name = prompt("Enter the Name of the new sensor:")
  if(new_sensor_name == null) {return;} // cancel when user chooses to cancel

  $.ajax({
    method: 'POST',
    url: host + "/sensors/" + new_sensor_name,

    success: function(response) {
      var db_id = response.data;
      console.log("added new sensor with name: " + new_sensor_name);
      window.location.reload();
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(addSensor);
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else if (status == 409){
        alert("Error: sensor with that name already exists.");
        console.log(status, response.responseText);
      }else {
        console.log("addSensor error: ", status, response.responseText);
      }
    },
  });
}

function removeSensor() {
  var sensor_name = prompt("Enter the sensorName to remove: ")
  if (sensor_name == null) {return;} // return if user cancels input

  $.ajax({
    method: 'DELETE',
    url: host + "/sensors/" + sensor_name,

    success: function(response) {
      console.log("deleted sensor with name " + sensor_name);
      var db_id = response.data;
      var row = document.getElementById("row-" + db_id);
      row.parentNode.removeChild(row);
    },
    error: function(response){
      var status = response.status;
      if (status == 401) {
        console.log("401: Unauthorized")
        perform_JWT_refresh().done(removeSensor);
      } else if (status == 403) {
        //redirect to login page
        alert("Insufficient rights.");
        console.log("403: Insufficient rights.")
      } else {
        console.log("removeSensor error: ", status, response.responseText);
      }
    },
  });
}

function update_location_list(){
  let text = "Update the sensor map?";
  if (confirm(text) != true) {
    return;
  }
  $.ajax({
    dataTypr: 'json',
    method: 'GET',
    url: host + "/sensors/update_locations",

    success: function(response) {
      sensors = response.data;
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
        console.log("sensors-autoload error: ", status, response.responseText);
      }
    },
  });
}