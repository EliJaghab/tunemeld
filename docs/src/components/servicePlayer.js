import { fetchAndDisplayChartData, hideChart } from "@/components/chart.js";

export function setupBodyClickListener(genre) {
  const body = document.body;
  if (!body) {
    console.error("Body element not found.");
    return;
  }

  body.addEventListener("click", (event) => {
    const link = event.target.closest("a");
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
}

export function setupClosePlayerButton() {
  const closeButton = document.getElementById("close-player-button");
  if (closeButton) {
    closeButton.addEventListener("click", closePlayer);
  } else {
    console.error("Close player button not found.");
  }
}

function handleLinkClick(event, link, genre, isrc) {
  const url = link.href;
  const serviceType = getServiceType(url);

  if (serviceType !== "none") {
    event.preventDefault();
    openPlayer(url, serviceType);
    window.scrollTo({ top: 0, behavior: "smooth" });

    if (isrc) {
      fetchAndDisplayChartData(genre, isrc);
    }
  }
}

function openPlayer(url, serviceType) {
  const placeholder = document.getElementById("service-player-placeholder");
  const closeButton = document.getElementById("close-player-button");

  placeholder.innerHTML = "";

  const iframe = document.createElement("iframe");
  iframe.width = "100%";
  iframe.style.border = "none";

  let showVolumeControl = false;

  switch (serviceType) {
    case "soundcloud":
      iframe.src = `https://w.soundcloud.com/player/?url=${encodeURIComponent(
        url,
      )}&auto_play=true`;
      iframe.allow = "autoplay";
      iframe.height = "166";
      showVolumeControl = true;
      break;
    case "spotify":
      const spotifyId = getSpotifyTrackId(url);
      iframe.src = `https://open.spotify.com/embed/${spotifyId}`;
      iframe.allow = "encrypted-media";
      iframe.height = "80";
      break;
    case "apple_music":
      const appleMusicId = getAppleMusicId(url);
      iframe.src = `https://embed.music.apple.com/us/album/${appleMusicId}`;
      iframe.allow = "autoplay *; encrypted-media *;";
      iframe.height = "175";
      break;
    case "youtube":
      iframe.src = `https://www.youtube.com/embed/${getYouTubeVideoId(
        url,
      )}?autoplay=1`;
      iframe.allow = "autoplay; encrypted-media";
      iframe.referrerPolicy = "no-referrer-when-downgrade";
      iframe.height = "315";
      break;
    default:
      console.error("Unsupported service type:", serviceType);
  }

  iframe.onload = function () {
    const playerContainer = document.getElementById("player-container");
    if (playerContainer) playerContainer.style.display = "block";
    closeButton.style.display = "block";
  };

  placeholder.appendChild(iframe);
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

  if (placeholder) placeholder.innerHTML = "";
  if (closeButton) closeButton.style.display = "none";
  if (playerContainer) playerContainer.style.display = "none";
  hideChart();
}

function getServiceType(url) {
  if (isSoundCloudLink(url)) return "soundcloud";
  if (isSpotifyLink(url)) return "spotify";
  if (isAppleMusicLink(url)) return "apple_music";
  if (isYouTubeLink(url)) return "youtube";
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

function getSpotifyTrackId(url) {
  const match = url.match(/\/(track|album|playlist)\/([a-zA-Z0-9]+)/);
  return match ? `${match[1]}/${match[2]}` : "";
}

function getAppleMusicId(url) {
  const match = url.match(/\/album\/[^\/]+\/(\d+)\?i=(\d+)/);
  return match ? `${match[1]}?i=${match[2]}` : "";
}

function getYouTubeVideoId(url) {
  const match = url.match(/v=([a-zA-Z0-9_-]+)/);
  return match ? match[1] : "";
}
