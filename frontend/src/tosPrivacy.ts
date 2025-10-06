import { stateManager } from "@/state/StateManager";

function acceptTosPrivacy(): void {
  const overlay = document.getElementById("tosPrivacyOverlay");
  if (overlay) {
    overlay.style.display = "none";
  }
  document.cookie = "tosPrivacyAccepted=true; path=/";
}

function checkTosPrivacyCookie(): string {
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

function handleTosPrivacyOverlay(): void {
  const overlay = document.getElementById("tosPrivacyOverlay");

  if (!overlay) return;

  if (checkTosPrivacyCookie() !== "true") {
    overlay.style.display = "block";
  } else {
    overlay.style.display = "none";
  }
}

export async function initializeTosPrivacyOverlay(): Promise<void> {
  const acceptButton = document.getElementById(
    "acceptButton",
  ) as HTMLButtonElement | null;
  if (!acceptButton) return;

  acceptButton.onclick = acceptTosPrivacy;

  // Get button labels from StateManager
  const acceptTermsLabels = stateManager.getButtonLabel("acceptTerms");

  if (acceptTermsLabels.length > 0) {
    const acceptLabel = acceptTermsLabels[0];
    if (acceptLabel.title) {
      acceptButton.title = acceptLabel.title;
    }
    if (acceptLabel.ariaLabel) {
      acceptButton.setAttribute("aria-label", acceptLabel.ariaLabel);
    }
  }

  handleTosPrivacyOverlay();
}
