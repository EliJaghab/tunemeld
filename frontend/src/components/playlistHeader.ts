/**
 * Playlist Header Management
 * Handles all header-related functionality including service art, descriptions, and modals
 */

import { SERVICE_NAMES } from "@/config/constants";
import { graphqlClient } from "@/services/graphql-client";
import { debugLog } from "@/config/config";
import { stateManager } from "@/state/StateManager";
import type { Playlist } from "@/types/index";

const headerDebug = (message: string, meta?: unknown) => {
  debugLog("Header", message, meta);
};

// Extend Window interface for HLS
declare global {
  interface Window {
    appleMusicHls?: any;
  }
}

// Declare HLS global
declare const Hls: any;

function isMobileView(): boolean {
  return window.innerWidth <= 480;
}

async function addMoreButtonLabels(
  moreButton: HTMLElement,
  serviceName: string,
): Promise<void> {
  try {
    // Map service names to button label keys
    const serviceToLabelKey: Record<
      string,
      keyof import("@/types").ButtonLabels
    > = {
      apple_music: "moreButtonAppleMusic",
      soundcloud: "moreButtonSoundcloud",
      spotify: "moreButtonSpotify",
      youtube: "moreButtonYoutube",
    };

    const labelKey = serviceToLabelKey[serviceName];
    if (!labelKey) {
      console.warn(`No button labels found for service: ${serviceName}`);
      return;
    }

    const buttonLabels = stateManager.getButtonLabel(labelKey);
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

function updateTuneMeldDescription(
  description: string | null | undefined,
): void {
  const descriptionElement = document.getElementById("playlist-description");
  if (descriptionElement && description) {
    descriptionElement.textContent = description;
  } else if (descriptionElement) {
    // Throw error instead of using fallback - this indicates missing curated description data
    const genre =
      window.location.search.match(/genre=([^&]+)/)?.[1] || "playlist";
    throw new Error(
      `Missing TuneMeld playlist description for genre: ${genre}. Expected curated description but received: ${description}`,
    );
  }
}

function displayAppleMusicVideo(url: string): Promise<void> {
  const videoContainer = document.getElementById("apple_music-video-container");
  if (!videoContainer) {
    return Promise.resolve();
  }

  cleanupExistingVideos();

  videoContainer.innerHTML = `
    <video id="apple_music-video" class="video-js vjs-default-skin" muted autoplay loop playsinline controlsList="nodownload nofullscreen noremoteplayback"></video>
  `;
  const video = document.getElementById(
    "apple_music-video",
  ) as HTMLVideoElement | null;

  return new Promise<void>((resolve) => {
    let notifiedReady = false;
    const notifyReady = (): void => {
      if (notifiedReady) return;
      notifiedReady = true;
      resolve();
    };

    if (video && typeof Hls !== "undefined" && Hls.isSupported()) {
      const hls = new Hls();
      window.appleMusicHls = hls; // Store globally for cleanup
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, function () {
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise.catch((error: Error) => {
            if (error.name !== "AbortError") {
              console.warn("Apple Music video play failed:", error);
            }
          });
        }
        notifyReady();
      });
      video.addEventListener("loadeddata", notifyReady, { once: true });
    } else if (video && video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.addEventListener("canplay", function () {
        const playPromise = video.play();
        if (playPromise !== undefined) {
          playPromise.catch((error: Error) => {
            if (error.name !== "AbortError") {
              console.warn("Apple Music video play failed:", error);
            }
          });
        }
        notifyReady();
      });
      video.addEventListener("loadeddata", notifyReady, { once: true });
    } else {
      notifyReady();
    }
  });
}

function cleanupExistingVideos(): void {
  // Stop any existing Apple Music videos to prevent AbortError
  const existingVideo = document.getElementById(
    "apple_music-video",
  ) as HTMLVideoElement | null;
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

function cleanupExistingModals(): void {
  // Use state manager to properly clean up modals
  stateManager.clearAllModals();
}

function createAndAttachModal(
  descriptionElement: HTMLElement,
  fullText: string,
  title: string,
  serviceName: string,
  genre: string,
  serviceIconUrl: string,
  playlistUrl: string,
): void {
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
  descriptionElement.addEventListener("click", function (event: Event) {
    event.preventDefault();
    event.stopPropagation();
    modal.classList.add("active");
    overlay.classList.add("active");
  });

  // If there's a more button, make it also open the modal
  const moreButton = descriptionElement.querySelector(
    ".more-button",
  ) as HTMLElement | null;
  if (moreButton) {
    // Add button labels from backend
    addMoreButtonLabels(moreButton as HTMLElement, serviceName);

    moreButton.addEventListener("click", function (event: Event) {
      event.preventDefault();
      event.stopPropagation();
      modal.classList.add("active");
      overlay.classList.add("active");
    });
  }

  const closeButton = modal.querySelector(
    ".description-modal-close",
  ) as HTMLElement | null;
  if (closeButton) {
    closeButton.title = "Close description";
    closeButton.setAttribute("aria-label", "Close description");
    closeButton.addEventListener("click", function () {
      modal.classList.remove("active");
      overlay.classList.remove("active");
    });
  }

  overlay.addEventListener("click", function () {
    modal.classList.remove("active");
    overlay.classList.remove("active");
  });
}

function setupDescriptionModal(
  descriptionElement: HTMLElement,
  description: string,
  title: string,
  serviceName: string,
  genre: string,
  serviceIconUrl: string,
  playlistUrl: string,
): void {
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

  const fullText = `${title}\n${description}`;

  if (description.length > estimatedMaxTextLength) {
    let truncatedText = description.substring(0, estimatedMaxTextLength);
    const lastSpaceIndex = truncatedText.lastIndexOf(" ");
    if (lastSpaceIndex > MIN_CHAR_LIMIT) {
      truncatedText = truncatedText.substring(0, lastSpaceIndex);
    }
    truncatedText += "... ";

    descriptionElement.innerHTML = `${truncatedText}<span class="more-button">more</span>`;
  } else {
    descriptionElement.innerHTML = description;
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

function toggleDescriptionExpand(event: Event): void {
  event.preventDefault();
  const descriptionElement = event.currentTarget as HTMLElement | null;
  if (descriptionElement && descriptionElement.classList.contains("expanded")) {
    descriptionElement.classList.remove("expanded");
  } else if (descriptionElement) {
    descriptionElement.classList.add("expanded");
  }
}

function preloadCoverImage(coverUrl: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    if (!coverUrl) {
      reject(new Error("Missing cover URL"));
      return;
    }

    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () =>
      reject(new Error(`Failed to load cover image: ${coverUrl}`));
    image.src = coverUrl;
  });
}

function getServiceOverlay(
  serviceContainer: HTMLElement | null,
): HTMLElement | null {
  if (!serviceContainer) return null;
  return serviceContainer.querySelector(
    ".loading-overlay",
  ) as HTMLElement | null;
}

function hideServiceHeaderShimmers(): void {
  headerDebug("hideServiceHeaderShimmers invoked");
  document
    .querySelectorAll<HTMLElement>(".service .loading-overlay")
    .forEach((overlay) => {
      overlay.classList.remove("active", "fade-out");
    });

  stateManager.hideShimmer("services");
}

async function updateServiceHeaderArt(
  service: string,
  coverUrl: string,
  playlistUrl: string,
  playlistName: string,
  playlistDescription: string,
  serviceName: string,
  genre: string,
  serviceIconUrl: string,
  displayCallback?: ((data: any) => void) | null,
): Promise<void> {
  headerDebug("updateServiceHeaderArt", {
    service,
    coverUrl,
    playlistUrl,
    playlistName,
  });
  const elementPrefix = service
    ? service.toLowerCase().replace(/\s+/g, "_")
    : "";

  const imagePlaceholder = document.getElementById(
    `${elementPrefix}-image-placeholder`,
  ) as HTMLElement | null;
  const titleDescriptionElement = document.getElementById(
    `${elementPrefix}-title-description`,
  ) as HTMLElement | null;
  const coverLinkElement = document.getElementById(
    `${elementPrefix}-cover-link`,
  );
  const serviceContainer = document.getElementById(elementPrefix);
  const overlay = getServiceOverlay(serviceContainer);

  const hasExistingContent =
    imagePlaceholder?.style.backgroundImage ||
    titleDescriptionElement?.textContent;

  if (hasExistingContent) {
    imagePlaceholder?.classList.add("header-hidden");
    titleDescriptionElement?.classList.add("header-hidden");
  }

  if (overlay) {
    overlay.classList.add("active");
  }

  if (hasExistingContent) {
    await new Promise((resolve) => setTimeout(resolve, 300));
  }

  let assetPromise: Promise<void> = Promise.resolve();

  if (coverUrl.endsWith(".m3u8") && service === SERVICE_NAMES.APPLE_MUSIC) {
    assetPromise = displayAppleMusicVideo(coverUrl).catch((error: unknown) => {
      headerDebug("service header apple music video failed", {
        service,
        coverUrl,
        error,
      });
    });
  } else if (imagePlaceholder && coverUrl) {
    const pendingToken = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    imagePlaceholder.dataset.pendingCover = pendingToken;

    assetPromise = preloadCoverImage(coverUrl)
      .then(() => {
        if (imagePlaceholder.dataset.pendingCover !== pendingToken) {
          return;
        }
        imagePlaceholder.style.backgroundImage = `url("${coverUrl}")`;
      })
      .catch((error: unknown) => {
        headerDebug("service header image failed", {
          service,
          coverUrl,
          error,
        });
      })
      .finally(() => {
        if (imagePlaceholder.dataset.pendingCover === pendingToken) {
          imagePlaceholder.dataset.pendingCover = "";
        }
      });
  }

  if (coverLinkElement) {
    (coverLinkElement as HTMLAnchorElement).href = playlistUrl;
  }

  if (titleDescriptionElement) {
    const combinedDescription = `${playlistName} · ${playlistDescription}`;
    setupDescriptionModal(
      titleDescriptionElement,
      combinedDescription,
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

  await assetPromise;
  headerDebug("service header asset ready", { service, coverUrl });

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      imagePlaceholder?.classList.remove("header-hidden");
      titleDescriptionElement?.classList.remove("header-hidden");
    });
  });
}

/**
 * Updates playlist header metadata
 * This is the single entry point for header updates to prevent duplicates
 */
export async function updatePlaylistHeader(
  genre: string,
  displayServiceCallback: ((data: any) => void) | null = null,
): Promise<void> {
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

    const serviceLoadPromises = serviceOrder.map((serviceName) => {
      const playlist = playlists.find((p) => p.serviceName === serviceName);
      if (playlist) {
        return updateServiceHeaderArt(
          serviceName,
          playlist.playlistCoverUrl || "",
          playlist.playlistUrl || "",
          playlist.playlistName || "",
          playlist.playlistCoverDescriptionText || "",
          playlist.serviceName,
          genre,
          playlist.serviceIconUrl || "",
          displayServiceCallback,
        );
      }

      console.warn(`No playlist data found for service: ${serviceName}`);
      return Promise.resolve();
    });

    const aggregatedPromise = Promise.all(serviceLoadPromises)
      .then(() => {
        headerDebug("service header batch resolved");
        hideServiceHeaderShimmers();
      })
      .catch((error) => {
        headerDebug("service header batch failed", { error });
        hideServiceHeaderShimmers();
      });
    stateManager.registerServiceHeaderReveal(aggregatedPromise);
  } catch (error) {
    console.error("Error fetching playlist metadata:", error);
    stateManager.registerServiceHeaderReveal(Promise.resolve());
    hideServiceHeaderShimmers();
    throw error;
  }
}

/**
 * Updates playlist header synchronously with existing data
 * Used when data is already fetched and we just need to update the DOM
 */
export function updatePlaylistHeaderSync(
  playlists: Playlist[],
  serviceOrder: string[],
  genre: string,
  displayServiceCallback: ((data: any) => void) | null = null,
): void {
  // Clean up any existing modals and videos when genre changes
  cleanupExistingModals();
  cleanupExistingVideos();

  const tuneMeldPlaylist = playlists.find(
    (p) => p.serviceName === SERVICE_NAMES.TUNEMELD,
  );
  updateTuneMeldDescription(tuneMeldPlaylist?.playlistCoverDescriptionText);

  const serviceLoadPromises = serviceOrder.map((serviceName) => {
    const playlist = playlists.find((p) => p.serviceName === serviceName);
    if (playlist) {
      return updateServiceHeaderArt(
        serviceName,
        playlist.playlistCoverUrl || "",
        playlist.playlistUrl || "",
        playlist.playlistName || "",
        playlist.playlistCoverDescriptionText || "",
        playlist.serviceName,
        genre,
        playlist.serviceIconUrl || "",
        displayServiceCallback,
      );
    }

    console.warn(`No playlist data found for service: ${serviceName}`);
    return Promise.resolve(() => {});
  });

  const aggregatedPromise = Promise.all(serviceLoadPromises)
    .then(() => {
      headerDebug("service header batch resolved (sync)");
      hideServiceHeaderShimmers();
    })
    .catch((error) => {
      headerDebug("service header batch failed", { error });
      hideServiceHeaderShimmers();
    });

  stateManager.registerServiceHeaderReveal(aggregatedPromise);
}
