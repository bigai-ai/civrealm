# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
var metamessage_changed = False
var logged_in_with_password = False
var captcha_site_key = '6LfpcgMTAAAAAPRAOqYy6ZUhuX6bOJ7-7-_1V0FL'
var password_reset_count = 0
var google_user_subject = None
"""
"""
/**************************************************************************
  Validate username callback
**************************************************************************/
function validate_username_callback()
{
  var check_username = $("#username_req").val()
  var result = False
  $.ajax({
   type: 'POST',
   url: "/validate_user?userstring=" + check_username,
   success: function(data, textStatus, request){
      if (data == "user_does_not_exist") {
        if (is_longturn()) {
          show_new_user_account_dialog()
          return
        }

        if (validate_username()) {
          network_init()
          if (!is_touch_device()) $("#pregame_text_input").focus()
          $("#dialog").dialog('close')
        }
      } else {
        username = $("#username_req").val().trim()
        var password = $("#password_req").val()
        if (password == None) {
          var stored_password = simpleStorage.get("password", "")
          if (stored_password != None and stored_password != False) {
            password = stored_password
          }
        }

        if (password != None and password.length > 2) {
          var shaObj = new jsSHA("SHA-512", "TEXT")
          shaObj.update(password)
          var sha_password = encodeURIComponent(shaObj.getHash("HEX"))

          $.ajax({
           type: 'POST',
           url: "/login_user?username=" + encodeURIComponent(username) + "&sha_password=" + sha_password,
           success: function(data, textStatus, request){
               if (data != None and data == "OK") {
                 simpleStorage.set("username", username)
                 simpleStorage.set("password", password)
                 /* Login OK! */
                 if (validate_username()) {
                   network_init()
                   if (!is_touch_device()) $("#pregame_text_input").focus()
                   $("#dialog").dialog('close')
                 }
                 logged_in_with_password = True
               } else {
                 $("#username_validation_result").html("Incorrect username or password. Please try again!")
                 $("#username_validation_result").show()
               }

             },
           error: function (request, textStatus, errorThrown) {
             swal("Login user failed.")
           }
          })
        } else {
          $("#username_validation_result").html("Player name already in use. Try a different player name, or enter the username and password of your account,<br> or create a new user account. <a class='pwd_reset' href='#' style='color: #bbbbbb'>Forgot password?</a>")
          $("#username_validation_result").show()
        }

        $("#password_row").show()
        $("#password_req").focus()
        $("#password_td").html("<input id='password_req' type='password' size='25' maxlength='200'>  &nbsp <a class='pwd_reset' href='#' style='color: #666666'>Forgot password?</a>")
        $(".pwd_reset").click(forgot_pbem_password)
      }
    },
   error: function (request, textStatus, errorThrown) {
     swal("Error. Please try again with a different name.")
   }
  })

}


/**************************************************************************
 Shows the create new user account with password dialog.
**************************************************************************/
function show_new_user_account_dialog(gametype)
{

  var title = "New user account"
  var message = "Create a new Freeciv-web user account with information about yourself:<br><br>"
                + "<table><tr><td>Username:</td><td><input id='username' type='text' size='25' maxlength='30' onkeyup='return forceLower(this)'></td></tr>"
                + "<tr><td>Email:</td><td><input id='email' type='email' size='25' maxlength='64' ></td></tr>"
                + "<tr><td>Password:</td><td><input id='password' type='password' size='25'></td></tr>"
                + "<tr><td>Confim password:</td><td><input id='confirm_password' type='password' size='25'></td></tr></table><br>"
                + "<div id='username_validation_result' style='display:none'></div><br>"
                + "Remember your username and password, since you will need this to log in later.<br><br>"
                + "Click to accept captcha to show that you are real human player:<br>"
                + "<div id='captcha_element'></div><br><br>"
                + "<div><small><ul><li>It is free and safe to create a new account on Freeciv-web.</li>"
                + "<li>A user account allows you to save and load games.</li>"
                + "<li>Other players can use your username to start Play-by-email games with you.</li>"
                + "<li>You will not receive any spam and your e-mail address will be kept safe. Your password is stored securely as a secure hash.</li>"
                + "<li>You can <a href='#' onclick='javascript:close_pbem_account()' style='color: black'>cancel</a> your account at any time if you want.</li>"
                + "</ul></small></div>"

  // reset dialog page.
  $("#dialog").remove()
  $("<div id='dialog'></div>").appendTo("div#game_page")

  $("#dialog").html(message)
  $("#dialog").attr("title", title)
  $("#dialog").dialog({
            bgiframe: True,
            modal: True,
            width: is_small_screen() ? "90%" : "60%",
            buttons:
            {
                "Cancel" : function() {
                    if (gametype == "pbem") {
                      show_pbem_dialog()
                    } else {
                      init_common_intro_dialog()
                    }
                },
                "Signup new user" : function() {
                    if (gametype == "pbem") {
                      create_new_freeciv_user_account_request("pbem")
                    } else {
                      create_new_freeciv_user_account_request("normal")
                    }

                }
            }
        })

  $("#dialog").dialog('open')

  if (grecaptcha !== undefined and grecaptcha != None) {
    $('#captcha_element').html('')
    grecaptcha.render('captcha_element', {
          'sitekey' : captcha_site_key
        })
  } else {
    swal("Captcha not available. This could be caused by a browser plugin.")
  }

  $("#username").blur(function() {
   $.ajax({
     type: 'POST',
     url: "/validate_user?userstring=" + $("#username").val(),
     success: function(data, textStatus, request) {
        if (data != "user_does_not_exist") {
          $("#username_validation_result").html("The username is already taken. Please choose another username.")
          $("#username_validation_result").show()
          $(".ui-dialog-buttonset button").button("disable")
        } else {
          $("#email").blur(function() {
          $.ajax({
            type: 'POST',
            url: "/validate_user?userstring=" + $("#email").val(),
            success: function(data, textStatus, request) {
               if (data == "invitation") {
                 $("#username_validation_result").html("")
                 $("#username_validation_result").hide()
                 $(".ui-dialog-buttonset button").button("enable")
               } else {
                 $("#username_validation_result").html("The e-mail is already registered. Please choose another.")
                 $("#username_validation_result").show()
                 $(".ui-dialog-buttonset button").button("disable")

               }
             }
           })
         })
        }
      }
    })
  })
}

/**************************************************************************
  This will try to create a new Freeciv-web user account with password.
**************************************************************************/
function create_new_freeciv_user_account_request(action_type)
{
  username = $("#username").val().trim().toLowerCase()
  var password = $("#password").val().trim()
  var confirm_password = $("#confirm_password").val().trim()
  var email = $("#email").val().trim()
  var captcha = $("#g-recaptcha-response").val()

  var cleaned_username = username.replace(/[^a-zA-Z]/g,'')

  $("#username_validation_result").show()
  if (!validateEmail(email)) {
    $("#username_validation_result").html("Invalid email address.")
    return False
  } else if (username == None or username.length == 0 or username == "pbem") {
    $("#username_validation_result").html("Your name can't be empty.")
    return False
  } else if (username.length <= 2 ) {
    $("#username_validation_result").html("Your name is too short.")
    return False
  } else if (password == None or password.length <= 2 ) {
    $("#username_validation_result").html("Your password is too short.")
    return False
  } else if (username.length >= 32) {
    $("#username_validation_result").html("Your name is too long.")
    return False
  } else if (username != cleaned_username) {
    $("#username_validation_result").html("Your name contains invalid characters, only the English alphabet is allowed.")
    return False
  } else if (password != confirm_password) {
    $("#username_validation_result").html("The passwords do not match.")
    return False
  } else if (captcha == None or captcha === undefined ) {
    $("#username_validation_result").html("Please fill in the captcha. You might have to disable some plugins to see the captcha.")
    return False
  }

  $("#username_validation_result").html("")
  $("#username_validation_result").hide()

  $("#dialog").parent().hide()

  var shaObj = new jsSHA("SHA-512", "TEXT")
  shaObj.update(password)
  var sha_password = urllib.parse.quote(shaObj.getHash("HEX"), safe='~()*!.\'')

  $.ajax({
   type: 'POST',
   url: "/create_pbem_user?username=" + encodeURIComponent(username) + "&email=" + encodeURIComponent(email)
            + "&password=" + sha_password + "&captcha=" + encodeURIComponent(captcha),
   success: function(data, textStatus, request){
       simpleStorage.set("username", username)
       simpleStorage.set("password", password)
       if (action_type == "pbem") {
         challenge_pbem_player_dialog("New account created. Your username is: " + username + ". You can now start a new PBEM game or wait for an invitation for another player.")
       } else {
         $("#dialog").dialog('close')
         network_init()
         logged_in_with_password = True
       }

      },
   error: function (request, textStatus, errorThrown) {
     $("#dialog").parent().show()
     swal("Creating new user failed.")
   }
  })
}

/**************************************************************************
  Customize nation: choose nation name and upload new flag.
**************************************************************************/
function show_customize_nation_dialog(player_id) {
  if (chosen_nation == -1 or client.conn['player_num'] == None
      or choosing_player == None or choosing_player < 0) return

  var pnation = nations[chosen_nation]

  // reset dialog page.
  $("#dialog").remove()
  $("<div id='dialog'></div>").appendTo("div#game_page")

  var message = "<br>New nation name: <input id='new_nation_adjective' type='text' size='30' value='" + pnation['adjective'] + "'><br><br>"
       + "Upload new flag: <input type='file' id='newFlagFileInput'><br><br>"
       + "For best results scale the image to 29 x 20 pixels before uploading. <br><br>"
       + "(Note: the customized nation and flag will only be active during the current game session and will not be visible to other players.)"

  $("#dialog").html(message)
  $("#dialog").attr("title", "Customize nation: " + pnation['adjective'])
  $("#dialog").dialog({
            bgiframe: True,
            modal: True,
            width: is_small_screen() ? "90%" : "50%",
            buttons:
            {
                "Cancel" : function() {
                  $("#dialog").dialog('close')
                  pick_nation(player_id)
                },
                "OK" : function() {
                    handle_customized_nation(player_id)
                }
            }
        })

  $("#dialog").dialog('open')
}


/**************************************************************************
  Recaptcha callback.
**************************************************************************/
function onloadCallback() {
  // recaptcha is ready and loaded.
}


/**************************************************************************
 Reset the password for the user.
**************************************************************************/
function forgot_pbem_password()
{

  var title = "Forgot your password?"
  var message = "Please enter your e-mail address to reset your password. Also complete the captcha. The new password will be sent to you by e-mail.<br><br>"
                + "<table><tr><td>E-mail address:</td><td><input id='email_reset' type='text' size='25'></td></tr>"
                + "</table><br><br>"
                + "<div id='captcha_element'></div>"
                + "<br><br>"

  // reset dialog page.
  $("#pwd_dialog").remove()
  $("<div id='pwd_dialog'></div>").appendTo("div#game_page")

  $("#pwd_dialog").html(message)
  $("#pwd_dialog").attr("title", title)
  $("#pwd_dialog").dialog({
            bgiframe: True,
            modal: True,
            width: is_small_screen() ? "80%" : "40%",
            buttons:
            {
                "Cancel" : function() {
                     $("#pwd_dialog").remove()
                },
                "Send password" : function() {
                    password_reset_count++
                    if (password_reset_count > 3) {
                      swal("Unable to reset password.")
                      return
                    }
                    var reset_email = $("#email_reset").val()
                    var captcha = $("#g-recaptcha-response").val()
                    if (reset_email == None or reset_email.length == 0 or captcha == None or captcha.length == 0) {
                      swal("Please fill in e-mail and complete the captcha.")
                      return
                    }
                    $.ajax({
                       type: 'POST',
                       url: "/reset_password?email=" + reset_email + "&captcha=" + encodeURIComponent(captcha),
                       success: function(data, textStatus, request){
                          swal("Password reset. Please check your email.")
                          $("#pwd_dialog").remove()
                        },
                       error: function (request, textStatus, errorThrown) {
                         swal("Error, password was not reset.")
                       }
                      })
                }
            }
        })

  $("#pwd_dialog").dialog('open')

  if (grecaptcha !== undefined and grecaptcha != None) {
    $('#captcha_element').html('')
    grecaptcha.render('captcha_element', {
          'sitekey' : captcha_site_key
        })
  } else {
    swal("Captcha not available. This could be caused by a browser plugin.")
  }

}

/**************************************************************************
 User signed in with Google account.
**************************************************************************/
function google_signin_on_success(googleUser)
{
  var id_token = googleUser.getAuthResponse().id_token
  username = $("#username_req").val().trim().toLowerCase()
  if (!validate_username()) {
    return
  }
  //validate user token.
  var xhr = new XMLHttpRequest()
  xhr.open('POST', '/token_signin')
  xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
  xhr.onload = function() {
    if (xhr.responseText == "Failed" or xhr.responseText == None or xhr.responseText.length < 5) {
      swal("Login failed.")
    } else if (xhr.responseText == "Email not verified") {
      swal("Login failed. E-mail not verified.")
    } else {
      google_user_subject = xhr.responseText
      simpleStorage.set("username", username)
      $("#dialog").dialog('close')
    }
  }
  xhr.send('idtoken=' + id_token + "&username=" + username)

}

def google_signin_on_failure(error):
    #Handle Google signin problems
    if error['error'] == "popup_closed_by_user":
        return

    swal("Unable to sign in with Google: " + JSON.stringify(error))
    console.error("Unable to sign in with Google: " + JSON.stringify(error))
"""
