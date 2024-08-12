
var overlay = document.getElementById("tosPrivacyOverlay");

var acceptButton = document.getElementById("acceptButton");

acceptButton.onclick = function() {
  overlay.style.display = "none";
  document.cookie = "tosPrivacyAccepted=true; path=/";
}

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
