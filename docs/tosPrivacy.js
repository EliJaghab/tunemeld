function acceptTosPrivacy() {
  const overlay = document.getElementById("tosPrivacyOverlay");
  overlay.style.display = "none";
  document.cookie = "tosPrivacyAccepted=true; path=/";
}

function checkTosPrivacyCookie() {
  const name = "tosPrivacyAccepted=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i].trim();
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function handleTosPrivacyOverlay() {
  const overlay = document.getElementById("tosPrivacyOverlay");
  
  if (checkTosPrivacyCookie() !== "true") {
    overlay.style.display = "block";
  } else {
    overlay.style.display = "none";
  }
}

export function initializeTosPrivacyOverlay() {
  const acceptButton = document.getElementById("acceptButton");
  acceptButton.onclick = acceptTosPrivacy;
  handleTosPrivacyOverlay();
}
