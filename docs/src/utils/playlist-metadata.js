import { graphqlClient } from "@/services/graphql-client.js";
import { SERVICE_NAMES } from "@/config/constants.js";

export function updatePlaylistMetadataSync(
  playlists,
  serviceOrder,
  genre,
  displayServiceCallback,
) {
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
        displayServiceCallback,
      );
    }
  });
}

export async function displayPlaylistMetadata(genre, displayServiceCallback) {
  try {
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

function updateServiceHeaderArt(
  service,
  coverUrl,
  playlistUrl,
  playlistName,
  playlistDescription,
  serviceName,
  genre,
  displayCallback,
) {
  // Map service names to HTML element ID prefixes
  const serviceIdMapping = {
    apple_music: "apple_music",
    soundcloud: "soundcloud",
    spotify: "spotify",
  };

  const elementPrefix = serviceIdMapping[service] || service.toLowerCase();

  const imagePlaceholder = document.getElementById(
    `${elementPrefix}-image-placeholder`,
  );
  const descriptionElement = document.getElementById(
    `${elementPrefix}-description`,
  );
  const titleElement = document.getElementById(
    `${elementPrefix}-playlist-title`,
  );
  const coverLinkElement = document.getElementById(
    `${elementPrefix}-cover-link`,
  );

  if (coverUrl.endsWith(".m3u8") && service === "apple_music") {
    displayAppleMusicVideo(coverUrl);
  } else if (imagePlaceholder) {
    imagePlaceholder.style.backgroundImage = `url('${coverUrl}')`;
  }

  if (titleElement) {
    titleElement.textContent = playlistName;
    titleElement.href = playlistUrl;
  }

  if (coverLinkElement) {
    coverLinkElement.href = playlistUrl;
  }

  if (descriptionElement) {
    setupDescriptionModal(
      descriptionElement,
      playlistDescription,
      playlistName,
      serviceName,
      genre,
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

function displayAppleMusicVideo(url) {
  const videoContainer = document.getElementById("apple_music-video-container");
  if (!videoContainer) return;

  videoContainer.innerHTML = `
    <video id="apple_music-video" class="video-js vjs-default-skin" muted autoplay loop playsinline controlsList="nodownload nofullscreen noremoteplayback"></video>
  `;
  const video = document.getElementById("apple_music-video");

  if (typeof Hls !== "undefined" && Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(url);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, function () {
      video.play();
    });
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    video.src = url;
    video.addEventListener("canplay", function () {
      video.play();
    });
  }
}

function setupDescriptionModal(
  descriptionElement,
  fullText,
  title,
  serviceName,
  genre,
) {
  descriptionElement.removeEventListener("click", toggleDescriptionExpand);

  const MIN_CHAR_LIMIT = 30;
  const descriptionBoxWidth = descriptionElement.clientWidth;

  let estimatedMaxTextLength;
  if (isMobileView()) {
    // Be more conservative on mobile to ensure MORE button is visible
    estimatedMaxTextLength = Math.max(
      MIN_CHAR_LIMIT,
      Math.min(50, Math.floor((descriptionBoxWidth / 8) * 1.2)),
    );
  } else {
    estimatedMaxTextLength = Math.max(
      MIN_CHAR_LIMIT,
      Math.floor((descriptionBoxWidth / 8) * 1.5) + 15,
    );
  }

  if (fullText.length > estimatedMaxTextLength) {
    let truncatedText = fullText.substring(0, estimatedMaxTextLength);
    const lastSpaceIndex = truncatedText.lastIndexOf(" ");
    if (lastSpaceIndex > MIN_CHAR_LIMIT) {
      truncatedText = truncatedText.substring(0, lastSpaceIndex);
    }
    truncatedText += "... ";

    descriptionElement.innerHTML = `${truncatedText}<span class="more-button">MORE</span>`;
    createAndAttachModal(
      descriptionElement,
      fullText,
      title,
      serviceName,
      genre,
    );
  } else {
    descriptionElement.textContent = fullText;
  }
}

function isMobileView() {
  return window.innerWidth <= 480;
}

function createAndAttachModal(
  descriptionElement,
  fullText,
  title,
  serviceName,
  genre,
) {
  const modal = document.createElement("div");
  modal.className = "description-modal";
  // Use textContent to avoid HTML injection and ensure full text displays
  const modalContent = document.createElement("div");
  modalContent.className = "description-modal-content";
  modalContent.textContent = fullText;

  modal.innerHTML = `
    <button class="description-modal-close">&times;</button>
    <div class="description-modal-header">${title}</div>
    <div class="description-modal-subheader">${serviceName} - ${genre}</div>
  `;
  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  const overlay = document.createElement("div");
  overlay.className = "description-overlay";
  document.body.appendChild(overlay);

  const moreButton = descriptionElement.querySelector(".more-button");
  if (moreButton) {
    moreButton.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      modal.classList.add("active");
      overlay.classList.add("active");
    });
  }

  modal
    .querySelector(".description-modal-close")
    .addEventListener("click", function () {
      modal.classList.remove("active");
      overlay.classList.remove("active");
    });

  overlay.addEventListener("click", function () {
    modal.classList.remove("active");
    overlay.classList.remove("active");
  });
}

function toggleDescriptionExpand() {
  this.classList.toggle("expanded");
}
