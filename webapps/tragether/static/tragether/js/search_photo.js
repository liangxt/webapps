var myIndex = 0;
function getPhoto() {
    var distination = $("#destination").text();
    var address = "https://www.googleapis.com/customsearch/v1?q=" + distination + "&cx=004585602816542746031:dhsk8ow6qry&key=AIzaSyCHLMQmFPekfa9Xs0FaBgniD9zb9iUQJF8&searchType=image";
    var img1 = $("<img id='img1' class='mySlides' height='200' width='300'>");
    var img2 = $("<img id='img2' class='mySlides' height='200' width='300'>");
    var img3 = $("<img id='img3' class='mySlides' height='200' width='300'>");
    var img4 = $("<img id='img1' class='mySlides' height='200' width='300'>");
    $.get(address)
        .done(function (data) {
            var json = data;
            var result = [];
            result[0] = "";
            result[1] = "";
            result[2] = "";
            result[3] = "";
            var index1 = 0;
            var index2 = 0;
            while(json.items != undefined && index1 < json.items.length && index2 <= 3) {
                if (json.items[index1].link != undefined) {
                    result[index2] = json.items[index1].link;
                    index2 = index2 + 1;
                    index1 = index1 + 1;
                } else {
                    index1 = index1 + 1;
                }
            }
            if (result[0] != "") {
                img1.attr('src', result[0]);
            } else {
                img1.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default1.jpeg");
            }
            if (result[1] != "") {
                img2.attr('src', result[1]);
            } else {
                img2.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default2.jpeg");
            }
            if (result[2] != "") {
                 img3.attr('src', result[2]);
            } else {
                 img3.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default3.jpeg");
            }
             if (result[3] != "") {
                 img4.attr('src', result[3]);
            } else {
                 img4.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default4.jpeg");
            }
        }).fail(function ()  {
            img1.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default1.jpeg");
            img2.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default2.jpeg");
            img3.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default3.jpeg");
            img4.attr('src', "https://s3.amazonaws.com/tragether/default/travel_pic/travel_default4.jpeg");
        });
    var group_img = $('#group_img');
    group_img.append(img1);
    group_img.append(img2);
    group_img.append(img3);
    group_img.append(img4);
}


function showPhoto() {
    var i;
    var x = $(".mySlides");
    for (i = 0; i < x.length; i++) {
       x[i].style.display = "none";
    }
    myIndex++;
    if (myIndex > x.length) {myIndex = 2}
    x[myIndex-1].style.display = "block";
    setTimeout(showPhoto, 2000);
}

function voteAttraction() {
    $("#vote_form").on('submit', function (event) {
        event.preventDefault();
        var attraction = $( "input:checked" ).val();
        var id = $(this).find("h2").text();
        $.ajax({
            url: "/tragether/vote_attraction",
            type: "POST",
            data: {new_vote: attraction, id: id},
            dataType: 'json',
            success: function (data) {
                $( "input").prop('checked', false);
                var status = data.status;
                if (status == '0') {
                    $('#error_message').text('You already vote for the attraction!');
                } else {
                    var result_bar = $('#result-bar');
                    result_bar.empty();
                    for (var i = 0; i < data.number.length; i++) {
                            var div1 = $('<div></div>');
                            var div2 = $('<div></div>');
                            div1.addClass('row');
                            div2.addClass('col-md-8');
                            var u = $('<ul></ul>');
                            var bar = $('<div></div>');
                            bar.addClass('progress');
                            var item = $('<div></div>');
                            item.addClass('progress-bar progress-bar-warning progress-bar-striped');
                            item.attr('aria-valuenow', '60');
                            item.attr('aria-valuemin', '0');
                            item.attr('aria-valuemax', '100');
                            item.css('width', String(data.number[i]) + '%');
                            item.text('  '+ data.attractions[i] + ' ' + data.number[i] + '%');
                            bar.append(item);
                            u.append(bar);
                            div2.append(u);
                            div1.append(div2);
                            result_bar.append(div1);
                    }
                }
            },
            error: function (xhr,errmsg,err) {
                 console.log(xhr.status + ": " + xhr.responseText);
            }

        });
    });
}

function inviteForm(){
    $('#invite-form').on('submit', function (event) {
        event.preventDefault();
        $('.invite_error').remove();
        $('#invite_message').text('');
        var id = $('#travel_id').text();
        var context = {};
        context['receiver'] = $('#id_receiver').find(":selected").val();
        context['subject'] = $('#id_subject').val();
        context['content'] = $('#invite_id_content').val();
        $.ajax({
            url: "/tragether/invite_travel/" + id,
            type: 'POST',
            data: context,
            dataType: 'json',
            success: function (data) {
                if (data.status != undefined) {
                    $('#myModal-invite').modal('hide');
                } else if(data.invite_message != undefined){
                    $('#myModal-invite').modal('show');
                    $("#invite_message").text(data.invite_message);
                } else {
                    $('#myModal-invite').modal('show');
                    if (data.invite_error.subject != undefined) {
                        var invite_error = $("<li class='error invite_error'>" + data.invite_error.subject[0] + "</li>");
                        invite_error.insertAfter($('#id_subject'));
                    }
                    if (data.invite_error.content != undefined) {
                        invite_error = $("<li class='error invite_error'>" + data.invite_error.content[0] + "</li>");
                        invite_error.insertAfter($('#invite_id_content'));
                    }
                    if (data.invite_error.receiver != undefined) {
                        invite_error = $("<li class='error invite_error'>" + data.invite_error.receiver[0] + "</li>");
                        invite_error.insertAfter($('#id_receiver'));
                    }
                }
            },
            error: function (xhr,errmsg,err) {
                 console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    });
}


$( document ).ready(function() {
    $('[data-toggle=tooltip]').tooltip();
    getPhoto();
    showPhoto();
    voteAttraction();
    inviteForm();
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
