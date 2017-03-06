$(document).ready(function() {
  $('.input-daterange').datepicker({
  	format: "yyyy-mm-dd",
  	autoclose: true,
  	todayHighlight: true,
    startDate: new Date()
  });
  $(".panel").each(function () {
  	var cur_div = $(this);
    var destination = $(this).attr("class").split(' ')[2];
    var address = "https://www.googleapis.com/customsearch/v1?q=" + destination + "&cx=017243472297052726553:8p21qqcmnca&key=AIzaSyCmu4CagDfUgv3DqdH5ekTRy-UbQCA31QU&searchType=image";
    $.get(address)
        .done(function (data) {
            var json = data;
            var result = "";
            var index = 0;
            while(json.items != undefined && index < json.items.length) {
                if (json.items[index].link != undefined) {
                    result = json.items[index].link;
                    break;
                }
                index = index + 1;
            }
            if (result != "") {
              $(cur_div).find("img").attr("src", result);
            } else {
              var num = Math.floor((Math.random() * 4) + 1);
              $(cur_div).find("img").attr("src", "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default" + num + ".jpeg");
            }
        }).fail(function ()  {
          var num = Math.floor((Math.random() * 4) + 1);
          $(cur_div).find("img").attr("src", "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default" + num + ".jpeg");
        });
  });
  function getCookie(name) {
      var cookieValue = null;
          if (document.cookie && document.cookie !== '') {
              var cookies = document.cookie.split(';');
              for (var i = 0; i < cookies.length; i++) {
              var cookie = jQuery.trim(cookies[i]);
                  if (cookie.substring(0, name.length + 1) === (name + '=')) {
                      cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                      break;
                  }
              }
          }
      return cookieValue;
  }
  var csrftoken = getCookie('csrftoken');
  function csrfSafeMethod(method) {
      return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
  });
});
