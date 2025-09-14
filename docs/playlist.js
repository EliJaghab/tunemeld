import { DJANGO_API_BASE_URL } from "./config.js";
import { stateManager } from "./StateManager.js";
import { graphqlClient } from "./graphql-client.js";
import { SERVICE_NAMES } from "./constants.js";

export function setupSortButtons() {
  document.querySelectorAll(".sort-controls .sort-button").forEach((button) => {
    button.addEventListener("click", function () {
      const sortType = button.getAttribute("data-sort");

      document
        .querySelectorAll(".sort-controls .sort-button")
        .forEach((btn) => {
          btn.classList.remove("active");
        });
      button.classList.add("active");

      let column = sortType;
      let order = "asc";

      if (sortType === "rank") {
        order = "asc";
      } else if (sortType === "youtube_views" || sortType === "spotify_views") {
        order = "desc";
      }

      stateManager.setCurrentColumn(column);
      stateManager.setCurrentOrder(order);
      sortTable(column, order, stateManager.getViewCountType());
    });
  });
}

export async function updateMainPlaylist(genre, viewCountType) {
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
      viewCountType,
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

async function fetchAndDisplayData(
  url,
  placeholderId,
  viewCountType,
  serviceName,
) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}. Status: ${response.status}`);
    }
    const responseData = await response.json();
    const data = responseData.data || responseData;
    playlistData = data;
    renderPlaylistTracks(data, placeholderId, viewCountType, serviceName);
  } catch (error) {
    console.error("Error fetching and displaying data:", error);
  }
}

function renderPlaylistTracks(
  playlists,
  placeholderId,
  viewCountType,
  serviceName,
) {
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
        ? createTuneMeldPlaylistTableRow(track, viewCountType)
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

function createTuneMeldPlaylistTableRow(track, viewCountType) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  rankCell.textContent = track.rank;

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

  const youtubeViews = track.youtubeCurrentViewCount;
  youtubeStatCell.textContent = youtubeViews
    ? youtubeViews.toLocaleString()
    : "";

  const spotifyStatCell = document.createElement("td");
  spotifyStatCell.className = "spotify-view-count";
  const spotifyViews = track.spotifyCurrentViewCount;
  spotifyStatCell.textContent = spotifyViews
    ? spotifyViews.toLocaleString()
    : "";

  const seenOnCell = document.createElement("td");
  seenOnCell.className = "seen-on";
  displaySources(seenOnCell, track);

  const externalLinksCell = document.createElement("td");
  externalLinksCell.className = "external";
  if (track.youtubeSource) {
    const youtubeLink = createSourceLinkFromService(track.youtubeSource);
    externalLinksCell.appendChild(youtubeLink);
  }

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  displayViewCounts(track, row, viewCountType);
  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function displayViewCounts(track, row, viewCountType) {
  const youtubeStatCell = document.createElement("td");
  youtubeStatCell.className = "youtube-view-count";

  const spotifyStatCell = document.createElement("td");
  spotifyStatCell.className = "spotify-view-count";

  const youtubeCurrentViewCount = track.youtubeCurrentViewCount;
  const spotifyCurrentViewCount = track.spotifyCurrentViewCount;

  switch (viewCountType) {
    case "total-view-count":
      youtubeStatCell.textContent = youtubeCurrentViewCount
        ? youtubeCurrentViewCount.toLocaleString()
        : "";
      spotifyStatCell.textContent = spotifyCurrentViewCount
        ? spotifyCurrentViewCount.toLocaleString()
        : "";
      break;

    case "weekly-view-count":
      youtubeStatCell.textContent = "";
      spotifyStatCell.textContent = "";
      break;

    default:
      console.error("Unknown view count type:", viewCountType);
      return;
  }

  row.appendChild(youtubeStatCell);
  row.appendChild(spotifyStatCell);
}

function createServicePlaylistTableRow(track, serviceName) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  rankCell.textContent = track.rank || "";

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

export function sortTable(column, order, viewCountType) {
  const sortedData = playlistData.map((playlist) => {
    playlist.tracks.sort((a, b) => {
      let aValue, bValue;

      if (column === "rank") {
        aValue = a.rank;
        bValue = b.rank;
      } else if (column === "spotify_views") {
        aValue = getViewCount(a, "Spotify", viewCountType);
        bValue = getViewCount(b, "Spotify", viewCountType);
      } else if (column === "youtube_views") {
        aValue = getViewCount(a, "Youtube", viewCountType);
        bValue = getViewCount(b, "Youtube", viewCountType);
      }

      return order === "asc" ? aValue - bValue : bValue - aValue;
    });
    return playlist;
  });

  renderPlaylistTracks(
    sortedData,
    "main-playlist-data-placeholder",
    viewCountType,
    SERVICE_NAMES.TUNEMELD,
  );
}

function getViewCount(track, platform, viewCountType) {
  let currentCount;
  if (platform === "Youtube" || platform === "YouTube") {
    currentCount = track.youtubeCurrentViewCount;
  } else if (platform === "Spotify" || platform === "spotify") {
    currentCount = track.spotifyCurrentViewCount;
  }

  if (viewCountType === "total-view-count") {
    return currentCount;
  } else if (viewCountType === "weekly-view-count") {
    return null;
  } else {
    console.error("Unknown view count type:", viewCountType);
    return null;
  }
}

export function resetCollapseStates() {
  document.querySelectorAll(".playlist-content").forEach((content) => {
    content.classList.remove("collapsed");
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
  content.classList.toggle("collapsed");
  button.textContent = content.classList.contains("collapsed") ? "▲" : "▼";
}
