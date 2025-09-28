/**
 * Playlist Header Management
 * Handles all header-related functionality including service art, descriptions, and modals
 */

import { SERVICE_NAMES } from "@/config/constants.js";
import { graphqlClient } from "@/services/graphql-client.js";
import { stateManager } from "@/state/StateManager.js";

function isMobileView() {
  return window.innerWidth <= 480;
}

async function addMoreButtonLabels(moreButton, serviceName) {
  try {
    const buttonLabels = await graphqlClient.getMiscButtonLabels(
      "more_button",
      serviceName,
    );
    if (buttonLabels && buttonLabels.length > 0) {
      const moreLabel = buttonLabels[0];
      if (moreLabel.title) {
        moreButton.title = moreLabel.title;
      }
      if (moreLabel.ariaLabel) {
        moreButton.setAttribute("aria-label", moreLabel.ariaLabel);
      }
    }
  } catch (error) {
    console.warn("Failed to load more button labels:", error);
    // Continue without labels if fetch fails
  }
}

function updateTuneMeldDescription(description) {
  const descriptionElement = document.getElementById("playlist-description");
  if (descriptionElement && description) {
    descriptionElement.textContent = description;
  } else if (descriptionElement) {
    // Set fallback text instead of leaving "Loading..."
    const genre =
      window.location.search.match(/genre=([^&]+)/)?.[1] || "playlist";
    descriptionElement.textContent = `TuneMeld ${
      genre.charAt(0).toUpperCase() + genre.slice(1)
    } Playlist`;
  }
}

function displayAppleMusicVideo(url) {
  const videoContainer = document.getElementById("apple_music-video-container");
  if (!videoContainer) return;

  cleanupExistingVideos();

  videoContainer.innerHTML = `
    <video id="apple_music-video" class="video-js vjs-default-skin" muted autoplay loop playsinline controlsList="nodownload nofullscreen noremoteplayback"></video>
  `;
  const video = document.getElementById("apple_music-video");

  if (typeof Hls !== "undefined" && Hls.isSupported()) {
    const hls = new Hls();
    window.appleMusicHls = hls; // Store globally for cleanup
    hls.loadSource(url);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, function () {
      // Add error handling for play() promise
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch((error) => {
          // Ignore AbortError when video is removed during genre switches
          if (error.name !== "AbortError") {
            console.warn("Apple Music video play failed:", error);
          }
        });
      }
    });
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = url;
    video.addEventListener("canplay", function () {
      // Add error handling for play() promise
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch((error) => {
          // Ignore AbortError when video is removed during genre switches
          if (error.name !== "AbortError") {
            console.warn("Apple Music video play failed:", error);
          }
        });
      }
    });
  }
}

function cleanupExistingVideos() {
  // Stop any existing Apple Music videos to prevent AbortError
  const existingVideo = document.getElementById("apple_music-video");
  if (existingVideo) {
    existingVideo.pause();
    existingVideo.removeAttribute("src");
    existingVideo.load(); // Reset the video element
  }

  // Clean up any existing HLS instances stored globally
  if (window.appleMusicHls) {
    window.appleMusicHls.destroy();
    window.appleMusicHls = null;
  }
}

function cleanupExistingModals() {
  // Use state manager to properly clean up modals
  stateManager.clearAllModals();
}

function createAndAttachModal(
  descriptionElement,
  fullText,
  title,
  serviceName,
  genre,
  serviceIconUrl,
  playlistUrl,
) {
  const modal = document.createElement("div");
  modal.className = "description-modal";

  const modalContent = document.createElement("div");
  modalContent.className = "description-modal-content";
  modalContent.textContent = fullText;

  modal.innerHTML = `
    <button class="description-modal-close">&times;</button>
    <div class="description-modal-header">
      <img src="${serviceIconUrl}" alt="${serviceName}" class="description-modal-icon" />
      <a href="${playlistUrl}" target="_blank" class="description-modal-title">${title}</a>
    </div>
  `;
  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  const overlay = document.createElement("div");
  overlay.className = "description-overlay";
  document.body.appendChild(overlay);

  // Register modal with state manager
  const modalId = `modal-${serviceName}-${genre}-${Date.now()}`;
  stateManager.registerModal(modalId, modal, overlay);

  // Make entire description clickable to open modal
  descriptionElement.style.cursor = "pointer";
  descriptionElement.addEventListener("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
    modal.classList.add("active");
    overlay.classList.add("active");
  });

  // If there's a more button, make it also open the modal
  const moreButton = descriptionElement.querySelector(".more-button");
  if (moreButton) {
    // Add button labels from backend
    addMoreButtonLabels(moreButton, serviceName);

    moreButton.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      modal.classList.add("active");
      overlay.classList.add("active");
    });
  }

  const closeButton = modal.querySelector(".description-modal-close");
  closeButton.title = "Close description";
  closeButton.setAttribute("aria-label", "Close description");
  closeButton.addEventListener("click", function () {
    modal.classList.remove("active");
    overlay.classList.remove("active");
  });

  overlay.addEventListener("click", function () {
    modal.classList.remove("active");
    overlay.classList.remove("active");
  });
}

function setupDescriptionModal(
  descriptionElement,
  fullText,
  title,
  serviceName,
  genre,
  serviceIconUrl,
  playlistUrl,
) {
  descriptionElement.removeEventListener("click", toggleDescriptionExpand);

  const MIN_CHAR_LIMIT = 30;
  const descriptionBoxWidth = descriptionElement.clientWidth;

  let estimatedMaxTextLength;
  if (isMobileView()) {
    // Show more text on mobile with larger font size
    estimatedMaxTextLength = Math.max(
      MIN_CHAR_LIMIT,
      Math.min(120, Math.floor((descriptionBoxWidth / 6) * 1.5)),
    );
  } else {
    // Target exactly 3 lines with "more" at end of 3rd line
    const avgCharsPerLine = Math.floor(descriptionBoxWidth / 9); // Aggressive to fill 3 lines
    const fullLines = 2; // First 2 lines completely full
    const partialLine = 0.7; // Most of 3rd line, leaving space for "more"
    const moreButtonSpace = 6; // Space for " more"
    estimatedMaxTextLength = Math.max(
      MIN_CHAR_LIMIT,
      Math.floor(avgCharsPerLine * (fullLines + partialLine) - moreButtonSpace),
    );
  }

  if (fullText.length > estimatedMaxTextLength) {
    let truncatedText = fullText.substring(0, estimatedMaxTextLength);
    const lastSpaceIndex = truncatedText.lastIndexOf(" ");
    if (lastSpaceIndex > MIN_CHAR_LIMIT) {
      truncatedText = truncatedText.substring(0, lastSpaceIndex);
    }
    truncatedText += "... ";

    // Check if this is a combined title-description format
    if (fullText.includes(" · ")) {
      const [titlePart, ...descParts] = fullText.split(" · ");
      const remainingDesc = descParts.join(" · ");
      if (truncatedText.includes(" · ")) {
        const [truncatedTitle, ...truncatedDescParts] =
          truncatedText.split(" · ");
        const truncatedDesc = truncatedDescParts.join(" · ");
        descriptionElement.innerHTML = `<strong>${truncatedTitle}</strong> · ${truncatedDesc}<span class="more-button">more</span>`;
      } else {
        descriptionElement.innerHTML = `<strong>${truncatedText}</strong><span class="more-button">more</span>`;
      }
    } else {
      descriptionElement.innerHTML = `${truncatedText}<span class="more-button">more</span>`;
    }
  } else {
    // Check if this is a combined title-description format
    if (fullText.includes(" · ")) {
      const [titlePart, ...descParts] = fullText.split(" · ");
      const remainingDesc = descParts.join(" · ");
      descriptionElement.innerHTML = `<strong>${titlePart}</strong> · ${remainingDesc}`;
    } else {
      descriptionElement.textContent = fullText;
    }
  }

  // Always create and attach modal, regardless of text length
  createAndAttachModal(
    descriptionElement,
    fullText,
    title,
    serviceName,
    genre,
    serviceIconUrl,
    playlistUrl,
  );
}

function toggleDescriptionExpand(event) {
  event.preventDefault();
  const descriptionElement = event.currentTarget;
  if (descriptionElement.classList.contains("expanded")) {
    descriptionElement.classList.remove("expanded");
  } else {
    descriptionElement.classList.add("expanded");
  }
}

function updateServiceHeaderArt(
  service,
  coverUrl,
  playlistUrl,
  playlistName,
  playlistDescription,
  serviceName,
  genre,
  serviceIconUrl,
  displayCallback,
) {
  const elementPrefix = service || service.toLowerCase();

  const imagePlaceholder = document.getElementById(
    `${elementPrefix}-image-placeholder`,
  );
  const titleDescriptionElement = document.getElementById(
    `${elementPrefix}-title-description`,
  );
  const coverLinkElement = document.getElementById(
    `${elementPrefix}-cover-link`,
  );

  if (coverUrl.endsWith(".m3u8") && service === SERVICE_NAMES.APPLE_MUSIC) {
    displayAppleMusicVideo(coverUrl);
  } else if (imagePlaceholder) {
    imagePlaceholder.style.backgroundImage = `url('${coverUrl}')`;
  }

  if (coverLinkElement) {
    coverLinkElement.href = playlistUrl;
  }

  if (titleDescriptionElement) {
    const combinedText = `${playlistName} · ${playlistDescription}`;
    setupDescriptionModal(
      titleDescriptionElement,
      combinedText,
      playlistName,
      serviceName,
      genre,
      serviceIconUrl,
      playlistUrl,
    );
  }

  if (displayCallback) {
    displayCallback({
      service,
      coverUrl,
      playlistUrl,
      playlistName,
      description: playlistDescription,
      serviceName,
      genre,
    });
  }
}

/**
 * Updates playlist header metadata
 * This is the single entry point for header updates to prevent duplicates
 */
export async function updatePlaylistHeader(
  genre,
  displayServiceCallback = null,
) {
  try {
    // Clean up any existing modals and videos when genre changes
    cleanupExistingModals();
    cleanupExistingVideos();
    const { serviceOrder, playlists } =
      await graphqlClient.getPlaylistMetadata(genre);

    const tuneMeldPlaylist = playlists.find(
      (p) => p.serviceName === SERVICE_NAMES.TUNEMELD,
    );
    updateTuneMeldDescription(tuneMeldPlaylist?.playlistCoverDescriptionText);

    serviceOrder.forEach((serviceName) => {
      const playlist = playlists.find((p) => p.serviceName === serviceName);
      if (playlist) {
        updateServiceHeaderArt(
          serviceName,
          playlist.playlistCoverUrl,
          playlist.playlistUrl,
          playlist.playlistName,
          playlist.playlistCoverDescriptionText,
          playlist.serviceName,
          genre,
          playlist.serviceIconUrl,
          displayServiceCallback,
        );
      } else {
        console.warn(`No playlist data found for service: ${serviceName}`);
      }
    });
  } catch (error) {
    console.error("Error fetching playlist metadata:", error);
    throw error;
  }
}

/**
 * Updates playlist header synchronously with existing data
 * Used when data is already fetched and we just need to update the DOM
 */
export function updatePlaylistHeaderSync(
  playlists,
  serviceOrder,
  genre,
  displayServiceCallback = null,
) {
  // Clean up any existing modals and videos when genre changes
  cleanupExistingModals();
  cleanupExistingVideos();

  const tuneMeldPlaylist = playlists.find(
    (p) => p.serviceName === SERVICE_NAMES.TUNEMELD,
  );
  updateTuneMeldDescription(tuneMeldPlaylist?.playlistCoverDescriptionText);

  serviceOrder.forEach((serviceName) => {
    const playlist = playlists.find((p) => p.serviceName === serviceName);
    if (playlist) {
      updateServiceHeaderArt(
        serviceName,
        playlist.playlistCoverUrl,
        playlist.playlistUrl,
        playlist.playlistName,
        playlist.playlistCoverDescriptionText,
        playlist.serviceName,
        genre,
        playlist.serviceIconUrl,
        displayServiceCallback,
      );
    }
  });
}
