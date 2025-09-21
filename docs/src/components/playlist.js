import { DJANGO_API_BASE_URL } from "@/config/config.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { graphqlClient } from "@/services/graphql-client.js";
import { SERVICE_NAMES, TUNEMELD_RANK_FIELD } from "@/config/constants.js";

export async function updateMainPlaylist(genre) {
  try {
    const response = await graphqlClient.getPlaylistTracks(
      genre,
      SERVICE_NAMES.TUNEMELD,
    );
    const data = [response.playlist];
    playlistData = data;

    renderPlaylistTracks(
      data,
      "main-playlist-data-placeholder",
      SERVICE_NAMES.TUNEMELD,
    );

    if (response?.playlist?.playlistCoverDescriptionText) {
      const descriptionElement = document.getElementById(
        "playlist-description",
      );
      if (descriptionElement) {
        descriptionElement.textContent =
          response.playlist.playlistCoverDescriptionText;
      }
    }
  } catch (error) {
    console.error("Error updating main playlist:", error);
  }
}

export async function fetchAndDisplayPlaylists(genre) {
  const { serviceOrder } = await graphqlClient.getPlaylistMetadata(genre);

  return fetchAndDisplayPlaylistsWithOrder(genre, serviceOrder);
}

export async function fetchAndDisplayPlaylistsWithOrder(genre, serviceOrder) {
  const promises = serviceOrder.map(async (service) => {
    try {
      const response = await graphqlClient.getPlaylistTracks(genre, service);
      const data = [response.playlist];
      renderPlaylistTracks(data, `${service}-data-placeholder`, null, service);
    } catch (error) {
      console.error(`Error fetching ${service} playlist:`, error);
    }
  });
  await Promise.all(promises);
}

async function fetchAndDisplayData(url, placeholderId, serviceName) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}. Status: ${response.status}`);
    }
    const responseData = await response.json();
    const data = responseData.data || responseData;
    playlistData = data;
    renderPlaylistTracks(data, placeholderId, serviceName);
  } catch (error) {
    console.error("Error fetching and displaying data:", error);
  }
}

export function renderPlaylistTracks(playlists, placeholderId, serviceName) {
  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.error(`Placeholder with ID ${placeholderId} not found.`);
    return;
  }

  placeholder.innerHTML = "";
  const isTuneMeldPlaylist = serviceName === SERVICE_NAMES.TUNEMELD;

  playlists.forEach((playlist) => {
    playlist.tracks.forEach((track) => {
      const row = isTuneMeldPlaylist
        ? createTuneMeldPlaylistTableRow(track)
        : createServicePlaylistTableRow(track, serviceName);
      placeholder.appendChild(row);
    });
  });
}

function getServiceUrl(track, serviceName) {
  switch (serviceName) {
    case SERVICE_NAMES.SPOTIFY:
      return track.spotifyUrl;
    case SERVICE_NAMES.APPLE_MUSIC:
      return track.appleMusicUrl;
    case SERVICE_NAMES.SOUNDCLOUD:
      return track.soundcloudUrl;
    case SERVICE_NAMES.YOUTUBE:
      return track.youtubeUrl;
    case SERVICE_NAMES.TUNEMELD:
      return (
        track.spotifyUrl ||
        track.appleMusicUrl ||
        track.soundcloudUrl ||
        track.youtubeUrl
      );
    default:
      return track.youtubeUrl;
  }
}

function createTuneMeldPlaylistTableRow(track) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  rankCell.textContent = track.tunemeldRank;

  const coverCell = document.createElement("td");
  coverCell.className = "cover";
  const albumCover = document.createElement("img");
  albumCover.className = "album-cover";
  albumCover.src = track.albumCoverUrl || "";
  albumCover.alt = "Album Cover";
  coverCell.appendChild(albumCover);

  const trackInfoCell = document.createElement("td");
  trackInfoCell.className = "info";
  const trackInfoDiv = document.createElement("div");
  trackInfoDiv.className = "track-info-div";

  const trackTitle = document.createElement("a");
  trackTitle.className = "track-title";
  trackTitle.href = getServiceUrl(track, SERVICE_NAMES.TUNEMELD) || "#";
  trackTitle.textContent = track.trackName || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artistName || "Unknown Artist";

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement("br"));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  const youtubeStatCell = document.createElement("td");
  youtubeStatCell.className = "youtube-view-count";

  const youtubeViews = track.youtubeCurrentViewCountAbbreviated;
  youtubeStatCell.textContent = youtubeViews || "";

  const spotifyStatCell = document.createElement("td");
  spotifyStatCell.className = "spotify-view-count";
  const spotifyViews = track.spotifyCurrentViewCountAbbreviated;
  spotifyStatCell.textContent = spotifyViews || "";

  const seenOnCell = document.createElement("td");
  seenOnCell.className = "seen-on";
  displaySources(seenOnCell, track);

  const externalLinksCell = document.createElement("td");
  externalLinksCell.className = "external";

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  displayViewCounts(track, row);
  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function createViewCountElement(viewCount, source, url = null) {
  const container = document.createElement("div");
  container.className = "view-count-container";

  const logo = document.createElement("img");
  logo.src = source.iconUrl;
  logo.alt = source.displayName;
  logo.className = "view-count-logo";

  const text = document.createElement("span");
  text.textContent =
    typeof viewCount === "string" ? viewCount : viewCount.toLocaleString();

  container.appendChild(logo);
  container.appendChild(text);

  if (url) {
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.style.textDecoration = "none";
    link.style.color = "inherit";
    link.appendChild(container);
    return link;
  }

  return container;
}

function displayViewCounts(track, row) {
  const youtubeStatCell = document.createElement("td");
  youtubeStatCell.className = "youtube-view-count";

  const spotifyStatCell = document.createElement("td");
  spotifyStatCell.className = "spotify-view-count";

  const youtubeCurrentViewCountAbbreviated =
    track.youtubeCurrentViewCountAbbreviated;
  const spotifyCurrentViewCountAbbreviated =
    track.spotifyCurrentViewCountAbbreviated;

  if (youtubeCurrentViewCountAbbreviated && track.youtubeSource) {
    const element = createViewCountElement(
      youtubeCurrentViewCountAbbreviated,
      track.youtubeSource,
      track.youtubeUrl,
    );
    youtubeStatCell.appendChild(element);
  }

  if (spotifyCurrentViewCountAbbreviated && track.spotifySource) {
    const element = createViewCountElement(
      spotifyCurrentViewCountAbbreviated,
      track.spotifySource,
      track.spotifyUrl,
    );
    spotifyStatCell.appendChild(element);
  }

  row.appendChild(youtubeStatCell);
  row.appendChild(spotifyStatCell);
}

function createServicePlaylistTableRow(track, serviceName) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  rankCell.textContent = track.tunemeldRank || "";

  const coverCell = document.createElement("td");
  coverCell.className = "cover";
  const albumCover = document.createElement("img");
  albumCover.className = "album-cover";
  albumCover.src = track.albumCoverUrl || "";
  albumCover.alt = "Album Cover";
  coverCell.appendChild(albumCover);

  const trackInfoCell = document.createElement("td");
  trackInfoCell.className = "info";
  const trackInfoDiv = document.createElement("div");
  trackInfoDiv.className = "track-info-div";

  const trackTitle = document.createElement("a");
  trackTitle.className = "track-title";
  trackTitle.href = getServiceUrl(track, serviceName) || "#";
  trackTitle.textContent = track.trackName || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artistName || "Unknown Artist";

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement("br"));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  const externalLinksCell = document.createElement("td");
  externalLinksCell.className = "external";
  if (track.youtubeSource) {
    const youtubeLink = createSourceLinkFromService(track.youtubeSource);
    externalLinksCell.appendChild(youtubeLink);
  }

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  row.appendChild(externalLinksCell);

  return row;
}

function displaySources(cell, track) {
  const sourcesContainer = document.createElement("div");
  sourcesContainer.className = "track-sources";

  const serviceSources = [
    track.spotifySource,
    track.appleMusicSource,
    track.soundcloudSource,
  ].filter((source) => source !== null && source !== undefined);

  serviceSources.forEach((source) => {
    const linkElement = createSourceLinkFromService(source);
    sourcesContainer.appendChild(linkElement);
  });

  cell.appendChild(sourcesContainer);
}

function createSourceLinkFromService(source) {
  if (!source.url) {
    return document.createTextNode("");
  }

  const sourceIcon = document.createElement("img");
  const linkElement = document.createElement("a");
  linkElement.href = source.url;
  linkElement.target = "_blank";
  sourceIcon.className = "source-icon";
  sourceIcon.src = source.iconUrl;
  sourceIcon.alt = source.displayName;
  linkElement.appendChild(sourceIcon);
  return linkElement;
}

let playlistData = [];

export function setPlaylistData(data) {
  playlistData = data;
}

export function sortTable(column, order) {
  const ranks = appRouter.getAvailableRanks();
  const rankConfig = ranks.find((rank) => rank.sortField === column);

  if (!rankConfig) {
    console.error(`Unknown sort column: ${column}`);
    return;
  }

  const sortedData = playlistData.map((playlist) => {
    playlist.tracks.sort((a, b) => {
      let aValue = a[rankConfig.dataField];
      let bValue = b[rankConfig.dataField];

      // Handle null/undefined values
      if (aValue == null) aValue = 0;
      if (bValue == null) bValue = 0;

      return order === "asc" ? aValue - bValue : bValue - aValue;
    });

    // Only reassign rank numbers if we're not sorting by tunemeld-rank
    // TuneMeld rank is special - it preserves the backend-computed positions
    // For all other sorts (spotify views, youtube views, etc.), assign new positions based on sort
    if (column !== TUNEMELD_RANK_FIELD) {
      playlist.tracks.forEach((track, index) => {
        track.tunemeldRank = index + 1;
      });
    }

    return playlist;
  });

  // Update the module-level data so subsequent operations work correctly
  playlistData = sortedData;

  renderPlaylistTracks(
    sortedData,
    "main-playlist-data-placeholder",
    SERVICE_NAMES.TUNEMELD,
  );
}

function getViewCount(track, platform) {
  if (platform === "Youtube" || platform === "YouTube") {
    return track.youtubeCurrentViewCount;
  } else if (platform === "Spotify" || platform === "spotify") {
    return track.spotifyCurrentViewCount;
  }
  return null;
}

export function resetCollapseStates() {
  document.querySelectorAll(".playlist-content").forEach((content) => {
    content.classList.remove("collapsed");
  });
  document.querySelectorAll(".playlist").forEach((playlist) => {
    playlist.classList.remove("collapsed");
  });
  document.querySelectorAll(".collapse-button").forEach((button) => {
    button.textContent = "▼";
  });
}

export function addToggleEventListeners() {
  document.querySelectorAll(".collapse-button").forEach((button) => {
    button.removeEventListener("click", toggleCollapse);
  });

  document.querySelectorAll(".collapse-button").forEach((button) => {
    button.addEventListener("click", toggleCollapse);
  });
}

function toggleCollapse(event) {
  const button = event.currentTarget;
  const targetId = button.getAttribute("data-target");
  const content = document.querySelector(`${targetId} .playlist-content`);
  const playlist = document.querySelector(targetId);
  content.classList.toggle("collapsed");
  playlist.classList.toggle("collapsed");
  button.textContent = content.classList.contains("collapsed") ? "▲" : "▼";
}
