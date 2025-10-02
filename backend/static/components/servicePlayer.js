import { SERVICE_NAMES } from "@/config/constants";
import { graphqlClient } from "@/services/graphql-client";
import { appRouter } from "@/routing/router";
let serviceConfigs = null;
let iframeConfigs = null;
let serviceButtonsCreated = false;
let bodyClickListenerSetup = false;
let currentIframe = null;
let currentService = null;
async function loadIframeConfigs() {
  if (!iframeConfigs) {
    iframeConfigs = await graphqlClient.getIframeConfigs();
  }
  return iframeConfigs;
}
async function createIframeForService(url, serviceType) {
  const iframe = document.createElement("iframe");
  iframe.width = "100%";
  iframe.style.border = "none";
  try {
    // Use backend service to generate iframe URL
    const iframeSrc = await graphqlClient.generateIframeUrl(serviceType, url);
    if (!iframeSrc) {
      console.error("Failed to generate iframe URL for:", serviceType, url);
      return iframe;
    }
    const configs = await loadIframeConfigs();
    const config = configs.find((c) => c.serviceName === serviceType);
    if (config) {
      iframe.src = iframeSrc;
      iframe.allow = config.allow;
      iframe.height = config.height.toString();
      if (config.referrerPolicy) {
        iframe.referrerPolicy = config.referrerPolicy;
      }
    } else {
      console.error("No iframe config found for service:", serviceType);
    }
  } catch (error) {
    console.error("Error creating iframe for service:", serviceType, error);
  }
  return iframe;
}
export function setupBodyClickListener(genre) {
  if (bodyClickListenerSetup) {
    return;
  }
  const body = document.body;
  if (!body) {
    console.error("Body element not found.");
    return;
  }
  body.addEventListener("click", (event) => {
    const link = event.target?.closest("a");
    if (link) {
      const shouldIntercept = shouldInterceptLink(link);
      if (!shouldIntercept) {
        return;
      }
      const row = link.closest("tr");
      const isrc = row ? row.getAttribute("data-isrc") : null;
      handleLinkClick(event, link, genre, isrc);
    }
  });
  bodyClickListenerSetup = true;
}
export async function openTrackFromUrl(genre, player, isrc) {
  try {
    const tracks = document.querySelectorAll("tr[data-isrc]");
    for (const row of Array.from(tracks)) {
      if (row.getAttribute("data-isrc") === isrc) {
        const trackData = JSON.parse(row.getAttribute("data-track") || "{}");
        const configs = await loadServiceConfigs();
        const serviceConfig = configs.find((config) => config.name === player);
        if (!serviceConfig || !serviceConfig.urlField) {
          console.warn(`Unknown service or missing urlField: ${player}`);
          continue;
        }
        const url = trackData[serviceConfig.urlField];
        if (url) {
          await openPlayer(url, player, trackData);
          window.scrollTo({ top: 0, behavior: "smooth" });
          return true;
        }
      }
    }
    console.warn(`Track with ISRC ${isrc} not found in current playlist`);
    return false;
  } catch (error) {
    console.error("Error opening track player:", error);
    return false;
  }
}
export async function setupClosePlayerButton() {
  const closeButton = document.getElementById("close-player-button");
  if (closeButton) {
    closeButton.addEventListener("click", closePlayer);
    // Add button labels from backend
    try {
      const buttonLabels =
        await graphqlClient.getMiscButtonLabels("close_player");
      if (buttonLabels && buttonLabels.length > 0) {
        const closeLabel = buttonLabels[0];
        if (closeLabel.title) {
          closeButton.title = closeLabel.title;
        }
        if (closeLabel.ariaLabel) {
          closeButton.setAttribute("aria-label", closeLabel.ariaLabel);
        }
      }
    } catch (error) {
      console.warn("Failed to load close button labels:", error);
      // Continue without labels if fetch fails
    }
  } else {
    console.error("Close player button not found.");
  }
}
async function handleLinkClick(event, link, genre, isrc) {
  const url = link.href;
  const serviceType = getServiceType(url);
  if (serviceType !== "none") {
    event.preventDefault();
    // Use centralized navigation to update URL and show player
    appRouter.navigateToTrack(genre, "tunemeld-rank", serviceType, isrc);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}
async function openPlayer(url, serviceType, trackData = null) {
  const placeholder = document.getElementById("service-player-placeholder");
  const closeButton = document.getElementById("close-player-button");
  const serviceButtonsContainer = document.getElementById(
    "service-buttons-container",
  );
  // Clear service buttons but preserve iframe state
  if (serviceButtonsContainer) {
    serviceButtonsContainer.innerHTML = "";
    serviceButtonsContainer.style.display = "none";
  }
  // Use centralized iframe management
  let iframe;
  if (currentIframe && currentService === serviceType) {
    // Reuse existing iframe for same service
    try {
      const iframeSrc = await graphqlClient.generateIframeUrl(serviceType, url);
      if (iframeSrc) {
        currentIframe.src = iframeSrc;
        iframe = currentIframe;
      } else {
        throw new Error("Failed to generate iframe URL");
      }
    } catch (error) {
      console.error("Error updating iframe src:", error);
      // Create new iframe
      if (placeholder) placeholder.innerHTML = "";
      iframe = await createIframeForService(url, serviceType);
      currentIframe = iframe;
      currentService = serviceType;
    }
  } else {
    // Create new iframe
    if (placeholder) placeholder.innerHTML = "";
    iframe = await createIframeForService(url, serviceType);
    currentIframe = iframe;
    currentService = serviceType;
  }
  iframe.onload = function () {
    const playerContainer = document.getElementById("player-container");
    if (playerContainer) playerContainer.style.display = "block";
    if (closeButton) closeButton.style.display = "block";
    if (trackData && trackData.trackName && trackData.artistName) {
      appRouter.updateTitleWithTrackInfo(
        trackData.trackName,
        trackData.artistName,
      );
    }
    // Dynamically inject vertical spacing before and after player controls
    const playerContent = document.getElementById("player-content");
    const playerControls = document.getElementById("player-controls");
    if (playerContent && playerControls) {
      // Remove any existing vertical spacing
      const existingSpacing =
        playerContent.querySelectorAll(".vertical-spacing");
      existingSpacing.forEach((spacing) => spacing.remove());
      // Add vertical spacing before controls
      const verticalSpacingBefore = document.createElement("div");
      verticalSpacingBefore.className = "vertical-spacing";
      playerContent.insertBefore(verticalSpacingBefore, playerControls);
      // Add vertical spacing after controls
      const verticalSpacingAfter = document.createElement("div");
      verticalSpacingAfter.className =
        "vertical-spacing player-controls-spacing";
      playerContent.appendChild(verticalSpacingAfter);
    }
    createServiceButtons(trackData);
  };
  if (placeholder) placeholder.appendChild(iframe);
}
async function switchPlayer(url, serviceType) {
  // Use centralized iframe management via openPlayer
  // This eliminates duplicate iframe creation logic
  await openPlayer(url, serviceType);
}
function shouldInterceptLink(link) {
  /// does not intercept service playlists links from the header art - only track links open on tunemeld
  const isHeaderLink =
    link.classList.contains("header-title") ||
    link.id?.includes("cover-link") ||
    link.id?.includes("playlist-title") ||
    link.id?.includes("playlist-link");
  if (isHeaderLink) {
    return false;
  }
  const isInTableRow = link.closest("tr") !== null;
  return isInTableRow;
}
function closePlayer() {
  const placeholder = document.getElementById("service-player-placeholder");
  const closeButton = document.getElementById("close-player-button");
  const playerContainer = document.getElementById("player-container");
  const serviceButtonsContainer = document.getElementById(
    "service-buttons-container",
  );
  const playerContent = document.getElementById("player-content");
  if (placeholder) placeholder.innerHTML = "";
  if (closeButton) closeButton.style.display = "none";
  // Reset centralized iframe state
  currentIframe = null;
  currentService = null;
  if (playerContainer) playerContainer.style.display = "none";
  if (serviceButtonsContainer) serviceButtonsContainer.style.display = "none";
  // Reset page title to current genre
  const currentGenre = appRouter.getCurrentGenre();
  if (currentGenre) {
    appRouter.updatePageTitle(currentGenre);
  }
  // Remove all dynamically injected vertical spacing
  if (playerContent) {
    const existingSpacing = playerContent.querySelectorAll(".vertical-spacing");
    existingSpacing.forEach((spacing) => spacing.remove());
  }
}
function getServiceType(url) {
  if (isSoundCloudLink(url)) return SERVICE_NAMES.SOUNDCLOUD;
  if (isSpotifyLink(url)) return SERVICE_NAMES.SPOTIFY;
  if (isAppleMusicLink(url)) return SERVICE_NAMES.APPLE_MUSIC;
  if (isYouTubeLink(url)) return SERVICE_NAMES.YOUTUBE;
  return "none";
}
function isSoundCloudLink(url) {
  return /^https:\/\/soundcloud\.com\/[a-zA-Z0-9-_]+\/[a-zA-Z0-9-_]+/.test(url);
}
function isSpotifyLink(url) {
  return /^https:\/\/open\.spotify\.com\/(track|album|playlist)\/[a-zA-Z0-9]+/.test(
    url,
  );
}
function isAppleMusicLink(url) {
  return /^https:\/\/music\.apple\.com\//.test(url);
}
function isYouTubeLink(url) {
  return /^https:\/\/(www\.)?youtube\.com\/watch\?v=[a-zA-Z0-9_-]+/.test(url);
}
async function loadServiceConfigs() {
  if (!serviceConfigs) {
    serviceConfigs = await graphqlClient.getServiceConfigs();
  }
  return serviceConfigs;
}
async function createServiceButtons(trackData) {
  const serviceButtonsContainer = document.getElementById(
    "service-buttons-container",
  );
  if (!serviceButtonsContainer || !trackData) return;
  // Force clear and hide first
  serviceButtonsContainer.innerHTML = "";
  serviceButtonsContainer.style.display = "none";
  const configs = await loadServiceConfigs();
  const addedUrls = new Set();
  for (const config of configs) {
    if (config.urlField && config.sourceField) {
      const url = trackData[config.urlField];
      const source = trackData[config.sourceField];
      if (url && source && !addedUrls.has(url)) {
        addedUrls.add(url);
        const button = document.createElement("button");
        button.className = "service-link-button";
        // Use backend button labels if available, otherwise fallback
        try {
          const buttonLabels = await graphqlClient.getMiscButtonLabels(
            "service_player_button",
            source.name,
          );
          if (buttonLabels && buttonLabels.length > 0) {
            const serviceLabel = buttonLabels[0];
            if (serviceLabel.title) {
              button.title = serviceLabel.title;
            }
            if (serviceLabel.ariaLabel) {
              button.setAttribute("aria-label", serviceLabel.ariaLabel);
            }
          } else {
            // Fallback to basic label
            button.title = `Play on ${source.displayName}`;
          }
        } catch (error) {
          console.warn("Failed to load service button labels:", error);
          button.title = `Play on ${source.displayName}`;
        }
        button.addEventListener("click", async () => {
          const serviceType = getServiceType(url);
          if (serviceType !== "none") {
            // Use centralized navigation to update URL
            const currentGenre = appRouter.getCurrentGenre();
            if (currentGenre) {
              appRouter.navigateToTrack(
                currentGenre,
                "tunemeld-rank",
                serviceType,
                trackData.isrc,
              );
            }
            window.scrollTo({ top: 0, behavior: "smooth" });
          }
        });
        const icon = document.createElement("img");
        icon.src = source.iconUrl;
        icon.alt = source.displayName;
        icon.className = "service-icon";
        button.appendChild(icon);
        serviceButtonsContainer.appendChild(button);
      }
    }
  }
  serviceButtonsContainer.style.display = "flex";
}
