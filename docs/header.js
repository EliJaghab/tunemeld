import { DJANGO_API_BASE_URL } from "./config.js";

export function showSkeletonLoaders() {
  document.querySelectorAll(".skeleton, .skeleton-text").forEach(el => {
    el.classList.add("loading");
  });
}

export function hideSkeletonLoaders() {
  document.querySelectorAll(".skeleton, .skeleton-text").forEach(el => {
    el.classList.remove("loading");
    el.classList.remove("skeleton");
    el.classList.remove("skeleton-text");
  });
}

export async function fetchAndDisplayHeaderArt(genre) {
  try {
    const response = await fetch(`${DJANGO_API_BASE_URL}/header-art/${genre}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch header art. Status: ${response.status}`);
    }
    const responseData = await response.json();
    
    // Handle Django's wrapped response format
    const data = responseData.data || responseData;
    displayHeaderArt(data);
  } catch (error) {
    console.error("Error fetching header art:", error);
  }
}

function displayHeaderArt(data) {
  const services = ["SoundCloud", "AppleMusic", "Spotify"];

  services.forEach(service => {
    const serviceData = data[service];
    if (serviceData) {
      const playlistCoverUrl = serviceData.playlist_cover_url;
      const playlistUrl = serviceData.playlist_url;
      const playlistName = serviceData.playlist_name;
      const playlistDescription = serviceData.playlist_cover_description_text;
      const serviceName = serviceData.service_name || service; // Use service name if not provided
      const genre = data.genre_name;

      displayServiceHeader(
        service,
        playlistCoverUrl,
        playlistUrl,
        playlistName,
        playlistDescription,
        serviceName,
        genre
      );
    } else {
      console.warn(`No data found for service: ${service}`);
    }
  });
}

function displayServiceHeader(service, coverUrl, playlistUrl, playlistName, playlistDescription, serviceName, genre) {
  const imagePlaceholder = document.getElementById(`${service.toLowerCase()}-image-placeholder`);
  const descriptionElement = document.getElementById(`${service.toLowerCase()}-description`);
  const titleElement = document.getElementById(`${service.toLowerCase()}-playlist-title`);
  const coverLinkElement = document.getElementById(`${service.toLowerCase()}-cover-link`);

  if (coverUrl.endsWith(".m3u8") && service === "AppleMusic") {
    displayAppleMusicVideo(coverUrl);
  } else {
    imagePlaceholder.style.backgroundImage = `url('${coverUrl}')`;
  }

  titleElement.textContent = playlistName;
  titleElement.href = playlistUrl;

  coverLinkElement.href = playlistUrl;

  setupDescriptionModal(descriptionElement, playlistDescription, playlistName, serviceName, genre);
}

function setupDescriptionModal(descriptionElement, fullText, title, serviceName, genre) {
  descriptionElement.removeEventListener("click", toggleDescriptionExpand);

  const descriptionBoxWidth = descriptionElement.clientWidth;

  // Use different max text lengths for mobile and desktop
  let estimatedMaxTextLength;
  if (isMobileView()) {
    estimatedMaxTextLength = Math.floor((descriptionBoxWidth / 8) * 1.5) + 10; // Adjust calculation for mobile
  } else {
    estimatedMaxTextLength = Math.floor((descriptionBoxWidth / 8) * 1.5) + 15; // Adjust calculation for desktop
  }

  if (fullText.length > estimatedMaxTextLength) {
    let truncatedText = fullText.substring(0, estimatedMaxTextLength);
    truncatedText = truncatedText.substring(0, truncatedText.lastIndexOf(" ")) + "... ";

    descriptionElement.innerHTML = `${truncatedText}<span class="more-button">MORE</span>`;
    createAndAttachModal(descriptionElement, fullText, title, serviceName, genre);
  } else {
    descriptionElement.textContent = fullText;
  }
}

function isMobileView() {
  return window.innerWidth <= 480;
}

function createAndAttachModal(descriptionElement, fullText, title, serviceName, genre) {
  const modal = document.createElement("div");
  modal.className = "description-modal";
  modal.innerHTML = `
    <button class="description-modal-close">&times;</button>
    <div class="description-modal-header">${title}</div>
    <div class="description-modal-subheader">${serviceName} - ${genre}</div>
    <div class="description-modal-content">${fullText}</div>
  `;
  document.body.appendChild(modal);

  const overlay = document.createElement("div");
  overlay.className = "description-overlay";
  document.body.appendChild(overlay);

  descriptionElement.querySelector(".more-button").addEventListener("click", function () {
    modal.classList.add("active");
    overlay.classList.add("active");
  });

  modal.querySelector(".description-modal-close").addEventListener("click", function () {
    modal.classList.remove("active");
    overlay.classList.remove("active");
  });

  overlay.addEventListener("click", function () {
    modal.classList.remove("active");
    overlay.classList.remove("active");
  });
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".description").forEach(descriptionElement => {
    const fullText = descriptionElement.textContent;
    setupDescriptionModal(descriptionElement, fullText);
  });
});

function toggleDescriptionExpand() {
  this.classList.toggle("expanded");
}

function displayAppleMusicVideo(url) {
  const videoContainer = document.getElementById("applemusic-video-container");
  videoContainer.innerHTML = `
    <video id="applemusic-video" class="video-js vjs-default-skin" muted autoplay loop playsinline controlsList="nodownload nofullscreen noremoteplayback"></video>
  `;
  const video = document.getElementById("applemusic-video");

  if (Hls.isSupported()) {
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
