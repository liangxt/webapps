// Map
function myGoogleMap() {
  // auto complete
  var input = (document.getElementById('id_place'));
  main_autocomplete = new google.maps.places.Autocomplete(input);
  coorArray = new Object()

  var mapCanvas = $("#map")[0];
  var mapOptions = {
    center: new google.maps.LatLng(0, 0),
    zoom: 1,
  };
  my_map = new google.maps.Map(mapCanvas, mapOptions);

  // populate chatbox msg list
  populateChatboxMSG();

  // channels
  setupSocket();

  // populate itinerary msg list
  populateItinerary();

  // directions
  directionsService = new google.maps.DirectionsService();
  directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});
  flightPath = new google.maps.Polyline({
    strokeColor: "#0000FF",
    strokeOpacity: 0.5,
    strokeWeight: 2
  });
}


// itinerary
function populateItinerary() {
  previous_correct_place = null
  all_markers = {}
  itinerary_list = $("#table-itinerary-display");
  $.get("/tragether/get-itinerary/" + id)
    .done(function(data) {
      itinerary_list.data('max-time', data['max-time']);
      if (data.itineraries.length > 0) {
        var latlngbounds = new google.maps.LatLngBounds();
      }
      for (var i = 0; i < data.itineraries.length; i++) {
          itinerary = data.itineraries[i];
          var new_itinerary = $(itinerary.html);
          new_itinerary.data("itinerary-id", itinerary.id);
          itinerary_list.append(new_itinerary);
          var lat = itinerary.latitude;
          var lng = itinerary.longitude;
          var coor = new google.maps.LatLng(lat, lng);
          latlngbounds.extend(coor);
          var marker = new google.maps.Marker({
            position:coor, 
            title:new_itinerary.find("td")[1].innerText.split(',')[0],
            start_time:itinerary.start_time
          });
          all_markers[itinerary.id] = marker;
          coorArray[itinerary.id] = coor;
          marker.setMap(my_map);

          // info window hover
          var infowindow = null
          marker.addListener('mouseover', function() {
            infowindow = new google.maps.InfoWindow({
              content: this.title
            });
            infowindow.open(my_map, this);
          });          
          marker.addListener('mouseout', function() {
            infowindow.close();
          });
      }
      if (data.itineraries.length > 0) {
        my_map.fitBounds(latlngbounds);
      }
      if (data.itineraries.length > 1) {
        generateDirections();
      }
    });
}


function generateDirections() {

  directionsDisplay.setMap(null);
  flightPath.setMap(null);

  // order the markers
  if (Object.keys(all_markers).length < 2) {
    return;
  }
  var items = Object.keys(all_markers).map(function(key) {
    return [key, all_markers[key].start_time];
  });
  items.sort(function(x1, x2) {
    return x1[1] > x2[1];
  });

  // get ordered way points 
  var coor_list = [];
  for (var i = 0; i < items.length; i++) {
    var marker_key = items[i][0];
    var marker = all_markers[marker_key];
    coor_list.push(marker.getPosition());
  }
  var waypts = [];
  for (var i = 1; i < coor_list.length - 1; i++) {
    waypts.push({
      location: coor_list[i],
      stopover: true
    });
  }

  // calculate the route
  directionsService.route({
    origin: coor_list[0],
    destination: coor_list[coor_list.length - 1],
    waypoints: waypts,
    optimizeWaypoints: true,
    travelMode: 'DRIVING'
  }, function(response, status) {
    if (status === 'OK') {
      directionsDisplay.setMap(my_map);
      directionsDisplay.setDirections(response);
    } else{
      // handle the situation when travel across ocean
      flightPath.setPath(coor_list);
      flightPath.setMap(my_map);
    }
  });
}


function findInsertionPoint(start_time) {
  var all_itineraries = $(itinerary_list.children());
  if (all_itineraries.length == 0) {
    return 0;
  } 
  for (i = 0; i < all_itineraries.length; i++) { 
    each_datetime = $(all_itineraries[i]).find('td')[0].innerText; 
    if (each_datetime >= start_time) {
      return i;
    }
  }
  return all_itineraries.length
}


function updateItinerary() {
  // get the current max_time on webpage
  var max_time = itinerary_list.data("max-time")
  if (max_time == undefined) {
    return;
  }
  if (max_time=="") {
    var url = "/tragether/update-itinerary/"+ id;
  } else {
    var url = "/tragether/update-itinerary/"+ id + "/" + max_time
  }
  $.get(url)
    .done(function(data) {
      itinerary_list.data('max-time', data['max-time']);
      for (var i = 0; i < data.itineraries.length; i++) {
        var itinerary = data.itineraries[i];
        // if has been deleted
        if (itinerary.deleted) {
          $("#itinerary_" + itinerary.id).remove();
          var marker = all_markers[itinerary.id];
          marker.setMap(null);
          delete coorArray[itinerary.id];
          delete all_markers[itinerary.id];
        } else {
          // if not deleted, just edited, delete the original one
          // if not deleted, just added, skip this deletion
          if ($("#itinerary_" + itinerary.id).length) {
            $("#itinerary_" + itinerary.id).remove();
            var marker = all_markers[itinerary.id];
            marker.setMap(null);
            delete coorArray[itinerary.id];
          }
          // add a new itinerary
          var new_itinerary = $(itinerary.html);
          new_itinerary.data("itinerary-id", itinerary.id);
          var position = findInsertionPoint(itinerary.start_time);
          if (position==0) {
            itinerary_list.prepend(new_itinerary);
          }
          else {
            new_itinerary.insertAfter($(itinerary_list).children().eq(position - 1));
          }
          // add the new marker
          var lat = itinerary.latitude;
          var lng = itinerary.longitude;
          var coor = new google.maps.LatLng(lat, lng);
          var marker = new google.maps.Marker({
            position:coor, 
            title:new_itinerary.find("td")[1].innerText.split(',')[0],
            start_time:itinerary.start_time
          });
          all_markers[itinerary.id] = marker;
          coorArray[itinerary.id] = coor;
          marker.setMap(my_map);
          marker.setAnimation(google.maps.Animation.BOUNCE);
          setTimeout(function(){ marker.setAnimation(null); }, 750);

          // info window hover
          var infowindow = null
          marker.addListener('mouseover', function() {
            infowindow = new google.maps.InfoWindow({
              content: this.title
            });
            infowindow.open(my_map, this);
          });          
          marker.addListener('mouseout', function() {
            infowindow.close();
          });
        }
      }
      if (data.itineraries.length > 0) {
        generateDirections();
        if (Object.keys(coorArray).length > 0) {
          var latlngbounds = new google.maps.LatLngBounds();
          for (var coor in coorArray) {
            latlngbounds.extend(coorArray[coor]);
          }
          my_map.fitBounds(latlngbounds);
        } else {
          my_map.setOptions({
            center: new google.maps.LatLng(0, 0),
            zoom: 1,
          });
        }
      }
    });
}


function addItinerary(){
  var placeField = $(".panel-body-itinerary").find("#id_place");
  var place = placeField.val();
  var starttimeField = $(".panel-body-itinerary").find("#itinerary-datetimepicker");
  var start_time = starttimeField.val();
  var errlst_place = $("#itinerary-place-error");
  errlst_place.empty();
  var errlst_starttime = $("#itinerary-starttime-error");
  errlst_starttime.empty();

  var cur_lat;
  var cur_lng;

  var cur_place = main_autocomplete.getPlace();

  if (cur_place == undefined) {
    if (previous_correct_place != place) {
      errlst_place.append($("<li>Please select a suggested place.</li>"));
      return;
    } else {
      cur_lat = previous_correct_lag;
      cur_lng = previous_correct_lng;      
    }
  } else if (cur_place.geometry) {
    cur_lat = cur_place.geometry.location.lat();
    cur_lng = cur_place.geometry.location.lng();
  }
  $.ajax({
      url : "/tragether/add-itinerary/" + id,
      type : "POST",
      data : {place:place, start_time:start_time, latitude:cur_lat, longitude:cur_lng},
      success : function(json) {
          if (json.content == 'valid') {
            placeField.val('');
            starttimeField.val('');
            updateItinerary();
            previous_correct_place = null
          }
          else {
            if ('place' in json) {
              errlst_place.append($("<li>" + json['place'] + "</li>"));
            }
            if ('start_time' in json) {
              errlst_starttime.append($("<li>" + json['start_time'] + "</li>"));
              if (!('place' in json)) {
                previous_correct_place = place;
                previous_correct_lag = cur_lat;
                previous_correct_lng = cur_lng;
              }
            }
          }
      },
  });
  main_autocomplete.set('place', null); // clear the place
}


function deleteItinerary(e){
  var itinerary_id = $(e).parent().attr("id");
  $.post("/tragether/delete-itinerary/" + itinerary_id)
    .done(function(data) {
      updateItinerary();
    });
}


function editItinerary(e){
  var this_modal = $(e).parent().parent().parent().parent();
  var itinerary_id = this_modal.data("itinerary-id")
  var edit_values = $(e).parent().prev()
  var place = $(edit_values).find('#id_place').val();
  var start_time = $(edit_values).find('#itinerary-datetimepicker').val();

  var errlst_place = $("#edit-itinerary-place-error");
  errlst_place.empty();
  var errlst_starttime = $("#edit-itinerary-starttime-error");
  errlst_starttime.empty();

  var cur_lat = 'None'
  var cur_lng = 'None'
  if (modal_place_before_any_change !=  place) {
    var cur_place = modal_autocomplete.getPlace();
    if (cur_place == undefined) {
      errlst_place.append($("<li>Please select a suggested place.</li>"));
      return;
    } else if (cur_place.geometry) {
      cur_lat = cur_place.geometry.location.lat();
      cur_lng = cur_place.geometry.location.lng();
    }
  }
  $.ajax({
      url : "/tragether/edit-itinerary/" + itinerary_id,
      type : "POST",
      data : {place:place, start_time:start_time, latitude:cur_lat, longitude:cur_lng},
      success : function(json) {
          if (json.content == 'valid') {
            $('#myModal-edit-itinerary').modal('hide');
            updateItinerary();
          }
          else {
            if ('place' in json) {
              errlst_place.append($("<li>" + json['place'] + "</li>"));
            }
            if ('start_time' in json) {
              errlst_starttime.append($("<li>" + json['start_time'] + "</li>"));
            }
          }
      },
  });
  main_autocomplete.set('place', null); // clear the place
}


// chatbox
function scroll_down() {
  $('#panel-body-chatbox').animate({
    scrollTop: $('#panel-body-chatbox').get(0).scrollHeight}, "fast");
}


function populateChatboxMSG() {
  id = $(".chatbox-input-container").attr("id");
  chatbox_msg_list = $("#panel-body-chatbox");
  $.get("/tragether/get-chatbox-msg/" + id)
    .done(function(data) {
      for (var i = 0; i < data.chat_msgs.length; i++) {
          chat_msg = data.chat_msgs[i];
          var new_chat_msg = $(chat_msg.html);
          chatbox_msg_list.append(new_chat_msg);
      }
      scroll_down();
    });
}


function setupSocket() {
  var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
  socket = new WebSocket(ws_scheme + '://' + window.location.host + "/chat?room="+id);
  socket.onmessage = function(e) {
    chatbox_msg_list.append(e.data);
    scroll_down();
  }
  if (socket.readyState==WebSocket.OPEN) socket.onopen();
}


function addChatboxMSG(){
  var msgField = $(".chatbox-input-container").find(".input-sm");
  var content = msgField.val();
  var errlst = $("#chatbox-error")
  errlst.empty();

  $.ajax({
      url : "/tragether/add-chatbox-msg/" + id,
      type : "POST",
      data : {content: content},
      success : function(json) {
          if (json.content == 'valid') {
            msgField.val('');
            socket.send(json.new_chat_msg_html);
          }
          else {
            for (i = 0; i < json.content.length; i++) {
              errlst.append($("<li>" + json.content[i] + "</li>"));
            }
          }
      },
  });
  scroll_down();
}


// main
$(document).ready(function () {

  // min and max the chatbox
  $(".container-chatbox").on('click', '.icon_minim', function () {
    var icon_minim = $(this);
    if (!icon_minim.hasClass('panel-collapsed')) {
      icon_minim.parents('.panel').find('.panel-body').slideUp();
      icon_minim.addClass('panel-collapsed');
      icon_minim.removeClass('glyphicon-minus').addClass('glyphicon-plus');
    } else {
      icon_minim.parents('.panel').find('.panel-body').slideDown();
      scroll_down();
      icon_minim.removeClass('panel-collapsed');
      icon_minim.removeClass('glyphicon-plus').addClass('glyphicon-minus');
    }
  });

  $(function () {
      $('#itinerary-datetimepicker').datetimepicker({
        autoclose: true,
        startDate: new Date()
      });
  });

  // chatbox send button action 
  $(".chatbox-btn-container").on("click", ".btn-chatbox", function() {
    addChatboxMSG();
  });

  // itinerary add button action 
  $(".panel-body-itinerary").on("click", ".btn-itinerary-add", function() {
    addItinerary();
  });

  // itinerary delete button action 
  $(".panel-body-itinerary").on("click", ".btn-itinerary-delete", function() {
    deleteItinerary(this);
  });

  
  // itinerary edit submit button action
  $("#myModal-edit-itinerary").on('click', ".btn-itinerary-edit-submit", function() {
    editItinerary(this);
  });


  // itinerary edit button action 
  $(".panel-body-itinerary").on("click", ".btn-itinerary-edit", function(e) {
    var itinerary_id = $(e.target).parents('td').attr('id');
    var current_values = $(e.target).parents('tr').children();
    var current_start_time = current_values[0].innerText;
    var current_place = current_values[1].innerText;
    modal_place_before_any_change = current_place
    var this_modal =  $("#myModal-edit-itinerary")
    this_modal.modal('show');
    this_modal.find('#id_place').val(current_place);
    this_modal.find('#itinerary-datetimepicker').val(current_start_time);
    this_modal.data('itinerary-id', itinerary_id);
    var errlst_place = this_modal.find("#edit-itinerary-place-error");
    errlst_place.empty();
    var errlst_starttime = this_modal.find("#edit-itinerary-starttime-error");
    errlst_starttime.empty();
    $("#myModal-edit-itinerary").find('#itinerary-datetimepicker').datetimepicker({
      autoclose: true,
      startDate: new Date()
    });
    var input = $("#myModal-edit-itinerary").find('#id_place')[0];
    modal_autocomplete = new google.maps.places.Autocomplete(input);
  });


  // travel edit submit button action
  $("#myModal-edit-travel").on('click', "#btn-travel-edit-submit", function(e) {
    e.preventDefault();
    var data_context = {}
    var this_modal = $(e.target).parents("#myModal-edit-travel");
    var destinationField = $(this_modal).find("#id_destination")
    data_context['destination'] = destinationField.val();
    var groupSizeField = $(this_modal).find("#id_group_size")
    data_context['group_size'] = groupSizeField.val();
    var startTimeField = $(this_modal).find("#id_start_time")
    data_context['start_time']  = startTimeField.val();
    var endTimeField = $(this_modal).find("#id_end_time")
    data_context['end_time']  = endTimeField.val();
    var budgetField = $(this_modal).find("#id_budget")
    data_context['budget']  = budgetField.val();
    var infoField = $(this_modal).find("#id_info")
    data_context['info']  = infoField.val();
    var statusField = $(this_modal).find("#id_status")
    data_context['status']  = statusField.val();

    var errlst_all = this_modal.find(".error");
    errlst_all.empty()

    $.ajax({
        url : "/tragether/edit_travel/" + id,
        type : "POST",
        data : data_context,
        success : function(json) {
            if (json.content == 'valid') {
              $(this_modal).modal('hide');
              window.location.replace("/tragether/travel_group/" + id);
            }
            else {
              if ('destination' in json) {
                error_message = $("<li class='error'>" + json['destination'] + "</li>")
                error_message.insertAfter(destinationField)
              }
              if ('group_size' in json) {
                error_message = $("<li class='error'>" + json['group_size'] + "</li>")
                error_message.insertAfter(groupSizeField)
              }
              if ('start_time' in json) {
                error_message = $("<li class='error'>" + json['start_time'] + "</li>")
                error_message.insertAfter(startTimeField)
              }
              if ('end_time' in json) {
                error_message = $("<li class='error'>" + json['end_time'] + "</li>")
                error_message.insertAfter(endTimeField)
              }
              if ('budget' in json) {
                error_message = $("<li class='error'>" + json['budget'] + "</li>")
                error_message.insertAfter(budgetField)
              }
              if ('info' in json) {
                error_message = $("<li class='error'>" + json['info'] + "</li>")
                error_message.insertAfter(infoField)
              }
              if ('status' in json) {
                error_message = $("<li class='error'>" + json['status'] + "</li>")
                error_message.insertAfter(statusField)
              }
              if ('__all__' in json) {
                error_message = $("<li class='error'>" + json['__all__'] + "</li>")
                error_message.insertAfter(endTimeField);
              }
            }
        },
    });
  });

   
  // update itinerary
  window.setInterval(updateItinerary, 6000);


  // CSRF set-up copied from Django docs
  function getCookie(name) {  
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  }
  var csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  });

});
