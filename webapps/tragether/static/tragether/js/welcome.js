$(document).ready(function () {
  if ($("#myModal-login").find(".error").text()) {
    $("#myModal-login").modal('show');
  } else if ($("#myModal-register").find(".error").text() || $("#myModal-register").find(".errorlist").length > 0) {
    $("#myModal-register").modal('show');
  } else if ($("#register-success").length > 0) {
    $("#myModal-confirmation").modal('show');
  } else if ($("#myModal-reset-password").find(".errorlist").length > 0) {
    $("#myModal-reset-password").modal('show');
  } else if ($("#reset-password-success").length > 0) {
    $("#myModal-confirmation").modal('show');
  } else if ($("#register-confirmed").length > 0) {
      $("#myModal-confirmation").modal('show');
  } else if ($("#reset-password-pswd").length > 0) {
      $("#myModal-reset-password-pswd").modal('show');
  } else if ($("#reset-password-confirmed").length > 0) {
      $("#myModal-confirmation").modal('show');
  } 
  $("#id_username").attr('placeholder', 'Username');
  $("#id_password").attr('placeholder', 'Password');
  $("#id_username").addClass('form-control');
  $("#id_password").addClass('form-control');
});
