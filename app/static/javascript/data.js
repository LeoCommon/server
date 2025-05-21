/*jshint esversion: 6*/

var sensorData = [];
var host = window.location.protocol + "//" + window.location.host;

document.getElementById("delete_all").onclick = deleteAll;
document.getElementById("logoutButton").onclick = logout;
document.getElementById("download_all").onclick = downloadAll;

window.onload = startCall();

function startCall() {
  $.ajax({
    dataTypr: 'array',
    method: 'GET',
    url: host + "/data/",

    success: function(response) {
      sensorData = response.data;
      console.log(sensorData);
      buildTable(sensorData);
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
        console.log("data-autoload error: ", status, response.responseText);
      }
    },
  });
}


function buildTable(data,showAll=false) {
  var table = document.getElementById('table_content');
  var default_number_of_items = 20;
  //only show newest 20 items if !showAll and we have more items
  if (showAll || default_number_of_items > data.length){
    var lastIndex = 0;
  }else{
    var lastIndex = data.length - default_number_of_items;
  }


  for (var i = data.length-1; i >=lastIndex; i--) {
    var entry = data[i];
    var row = `
      <tr id="row-${entry.id}">
        <td class="columns_with_ellipsis_overflow" style="padding:0 5px 0 5px">${entry.file_name}</td>
        <td style="padding:0 5px 0 5px">${entry.size}</td>
        <td class="columns_with_ellipsis_overflow" style="padding:0 5px 0 5px">${entry.sensor_name}</td>
        <td class="columns_with_ellipsis_overflow" style="padding:0 5px 0 5px">${entry.job_name}</td>
        <td class="buttonColumn" align="center" style="padding:0 5px 0 5px">
          <button class="remove_btn small_buttons" type="button" data-id=${entry.id} data-name=${entry.file_name} id="delete-${entry.id}">Delete</button>
          <button class="small_buttons" type="button" data-id=${entry.id} data-name=${entry.file_name} id="download-${entry.id}">Download</button>
          
        </td>
      </tr> `;

    $(`#table_content`).append(row);
    $(`#delete-${entry.id}`).on('click', deleteEntry);
    $(`#download-${entry.id}`).on('click', downloadEntry);
    document.getElementById("download-"+entry.id).setAttribute("href",host + "/data/download/" + entry.id);
  }
  if (!showAll && data.length > default_number_of_items){
    /*if not all elements are loaded, show "show all" button */
    var show_more_button = '<button class="small_buttons" type="button" id="show_all_button" style="left: 50%;margin: 5px auto;text-align:center;display:block;">Show all entries</button>';
    $('#table').after(show_more_button);
    $(`#show_all_button`).on('click', function(){
      document.getElementById('table_content').innerHTML = ''; /*clear table*/
      document.getElementById('show_all_button').remove();
      buildTable(data,true); /*rebuilt table with all elements*/
    });

  }
}

function downloadAll(){
  //ask before downloading all files
  if (confirm ('Download all files?')) {
    location.href = 'data/download';
}
return false;
}

function downloadEntry(){
  //ask before downloading all files
  var data_id = $(this).data('id');
  if (confirm (`Download file: ${$(this).data('name')}?`)) {
    location.href = 'data/download/'+data_id;
}
return false;
}


function deleteEntry() {
  var data_id = $(this).data('id');
  var row = $(`#row-${data_id}`);

  let text = `Delete file: ${$(this).data('name')}?` ;
  if (confirm(text) == true) {

    $.ajax({
      method: 'DELETE',
      url: host + "/data/" + data_id,
      dataTypr: 'json',

      success: function(response) {
        alert(response.data);
        console.log("delete successful");
        row.remove();
      },
      error: function(response){
        var status = response.status;
        if (status == 401) {
          console.log("401: Unauthorized")
          perform_JWT_refresh().done(deleteEntry);
        } else if (status == 403) {
          //redirect to login page
          alert("Insufficient rights.");
          console.log("403: Insufficient rights.")
        } else {
          console.log("deleteEntry error: ", status, response.responseText);
        }
      },
    });
  }
}

function deleteAll() {
  let text = "Delete all files?";
  if (confirm(text) == true) {
    $.ajax({
      method: 'DELETE',
      url: host + "/data/",

      success: function(response) {
        alert(response.data);
        console.log("delete all successful");
        $(`#table_content tr`).remove();
      },
      error: function(response){
        var status = response.status;
        if (status == 401) {
          console.log("401: Unauthorized")
          perform_JWT_refresh().done(deleteAll);
        } else if (status == 403) {
          //redirect to login page
          alert("Insufficient rights.");
          console.log("403: Insufficient rights.")
        } else {
          console.log("deleteAll error: ", status, response.responseText);
        }
      },
    });
  }
}



