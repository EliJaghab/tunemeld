function acceptTosPrivacy() {
  const overlay = document.getElementById("tosPrivacyOverlay");
  overlay.style.display = "none";
  document.cookie = "tosPrivacyAccepted=true; path=/";
}

function checkTosPrivacyCookie() {
  const name = "tosPrivacyAccepted=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(";");

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

export async function initializeTosPrivacyOverlay() {
  const acceptButton = document.getElementById("acceptButton");
  acceptButton.onclick = acceptTosPrivacy;

  // Add button labels from backend
  try {
    const { graphqlClient } = await import("./src/services/graphql-client.js");
    const buttonLabels =
      await graphqlClient.getMiscButtonLabels("accept_terms");
    if (buttonLabels && buttonLabels.length > 0) {
      const acceptLabel = buttonLabels[0];
      if (acceptLabel.title) {
        acceptButton.title = acceptLabel.title;
      }
      if (acceptLabel.ariaLabel) {
        acceptButton.setAttribute("aria-label", acceptLabel.ariaLabel);
      }
    }
  } catch (error) {
    console.warn("Failed to load accept button labels:", error);
    // Continue without labels if fetch fails
  }

  handleTosPrivacyOverlay();
}
