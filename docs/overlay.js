// Get the overlay
var overlay = document.getElementById("tosPrivacyOverlay");

// Get the button that accepts the terms
var acceptButton = document.getElementById("acceptButton");

// When the user clicks the button, hide the overlay and set a cookie
acceptButton.onclick = function() {
  overlay.style.display = "none";
  document.cookie = "tosPrivacyAccepted=true; path=/";
}

// Check if the cookie exists
function checkCookie() {
  var name = "tosPrivacyAccepted=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

// If the cookie does not exist, show the overlay
if (checkCookie() !== "true") {
  overlay.style.display = "block";
} else {
  overlay.style.display = "none";
}
