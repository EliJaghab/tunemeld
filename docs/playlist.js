import { DJANGO_API_BASE_URL, getAggregatePlaylistEndpoint, getServicePlaylistEndpoint } from "./config.js?v=20250828c";
import { stateManager } from "./StateManager.js";
import { graphqlClient } from "./graphql-client.js";

export async function fetchAndDisplayLastUpdated(genre) {
  try {
    const response = await fetch(`${DJANGO_API_BASE_URL}/last-updated/${genre}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch last-updated. Status: ${response.status}`);
    }
    const responseData = await response.json();
    // Handle Django's wrapped response format
    const lastUpdated = responseData.data || responseData;
    displayLastUpdated(lastUpdated);
  } catch (error) {
    console.error("Error fetching last updated date:", error);
  }
}

function displayLastUpdated(lastUpdated) {
  const lastUpdatedDate = new Date(lastUpdated.last_updated);
  const formattedDate = lastUpdatedDate.toLocaleString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  });
  document.getElementById("last-updated").textContent = `Last Updated - ${formattedDate}`;
}

export function setupSortButtons() {
  document.querySelectorAll(".sort-button").forEach(button => {
    button.addEventListener("click", function () {
      const column = button.getAttribute("data-column");
      const order = button.getAttribute("data-order");
      const newOrder = order === "desc" ? "asc" : "desc";
      button.setAttribute("data-order", newOrder);
      stateManager.setCurrentColumn(column);
      stateManager.setCurrentOrder(newOrder);
      sortTable(column, newOrder, stateManager.getViewCountType());
    });
  });
}

export async function updateMainPlaylist(genre, viewCountType) {
  try {
    const url = getAggregatePlaylistEndpoint(genre);
    await fetchAndDisplayData(url, "main-playlist-data-placeholder", true, viewCountType);
  } catch (error) {
    console.error("Error updating main playlist:", error);
  }
}

export async function fetchAndDisplayPlaylists(genre) {
  const services = await graphqlClient.getAvailableServices();
  const promises = services.map(service => {
    const url = getServicePlaylistEndpoint(genre, service);
    return fetchAndDisplayData(url, `${service.toLowerCase()}-data-placeholder`);
  });
  await Promise.all(promises);
}

async function fetchAndDisplayData(url, placeholderId, isAggregated = false, viewCountType) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}. Status: ${response.status}`);
    }
    const responseData = await response.json();
    // Handle Django's wrapped response format
    const data = responseData.data || responseData;
    playlistData = data;
    displayData(data, placeholderId, isAggregated, viewCountType);
  } catch (error) {
    console.error("Error fetching and displaying data:", error);
  }
}

function displayData(data, placeholderId, isAggregated = false, viewCountType) {
  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.error(`Placeholder with ID ${placeholderId} not found.`);
    return;
  }
  placeholder.innerHTML = "";
  data.forEach(playlist => {
    playlist.tracks.forEach(track => {
      const row = isAggregated
        ? createTableRow(track, isAggregated, viewCountType)
        : createSmallPlaylistTableRow(track);
      placeholder.appendChild(row);
    });
  });
}

function createTableRow(track, isAggregated, viewCountType) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  rankCell.textContent = track.rank;

  const coverCell = document.createElement("td");
  coverCell.className = "cover";
  const albumCover = document.createElement("img");
  albumCover.className = "album-cover";
  albumCover.src = track.album_cover_url || "";
  albumCover.alt = "Album Cover";
  coverCell.appendChild(albumCover);

  const trackInfoCell = document.createElement("td");
  trackInfoCell.className = "info";
  const trackInfoDiv = document.createElement("div");
  trackInfoDiv.className = "track-info-div";

  const trackTitle = document.createElement("a");
  trackTitle.className = "track-title";
  trackTitle.href = track.youtube_url || "#";
  trackTitle.textContent = track.track_name || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artist_name || "Unknown Artist";

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement("br"));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  const youtubeStatCell = document.createElement("td");
  youtubeStatCell.className = "youtube-view-count";

  // Handle both production (MongoDB) and dev (PostgreSQL) data structures
  const youtubeViews =
    track.view_count_data_json?.Youtube?.current_count_json?.current_view_count ||
    track.view_count_data_json?.YouTube?.current_count_json?.current_view_count ||
    0;
  youtubeStatCell.textContent = youtubeViews.toLocaleString();

  const spotifyStatCell = document.createElement("td");
  spotifyStatCell.className = "spotify-view-count";
  const spotifyViews =
    track.view_count_data_json?.Spotify?.current_count_json?.current_view_count ||
    track.view_count_data_json?.spotify?.current_count_json?.current_view_count ||
    0;
  spotifyStatCell.textContent = spotifyViews.toLocaleString();

  const seenOnCell = document.createElement("td");
  seenOnCell.className = "seen-on";
  if (isAggregated) {
    displaySources(seenOnCell, track);
  }

  const externalLinksCell = document.createElement("td");
  externalLinksCell.className = "external";
  if (track.youtube_url) {
    const youtubeLink = createSourceLink("YouTube", track.youtube_url);
    externalLinksCell.appendChild(youtubeLink);
  }

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  if (isAggregated) {
    displayViewCounts(track, row, viewCountType);
  }
  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function displayViewCounts(track, row, viewCountType) {
  const youtubeStatCell = document.createElement("td");
  youtubeStatCell.className = "youtube-view-count";

  const spotifyStatCell = document.createElement("td");
  spotifyStatCell.className = "spotify-view-count";

  const youtubeCurrentViewCount =
    track.view_count_data_json?.Youtube?.current_count_json?.current_view_count ||
    track.view_count_data_json?.YouTube?.current_count_json?.current_view_count ||
    0;
  const youtubeInitialViewCount =
    track.view_count_data_json?.Youtube?.initial_count_json?.initial_view_count ||
    track.view_count_data_json?.YouTube?.initial_count_json?.initial_view_count ||
    0;
  const spotifyCurrentViewCount =
    track.view_count_data_json?.Spotify?.current_count_json?.current_view_count ||
    track.view_count_data_json?.spotify?.current_count_json?.current_view_count ||
    0;
  const spotifyInitialViewCount =
    track.view_count_data_json?.Spotify?.initial_count_json?.initial_view_count ||
    track.view_count_data_json?.spotify?.initial_count_json?.initial_view_count ||
    0;

  switch (viewCountType) {
    case "total-view-count":
      youtubeStatCell.textContent = youtubeCurrentViewCount.toLocaleString();
      spotifyStatCell.textContent = spotifyCurrentViewCount.toLocaleString();
      break;

    case "weekly-view-count":
      const youtubeWeeklyViewCount = youtubeCurrentViewCount - youtubeInitialViewCount;
      const spotifyWeeklyViewCount = spotifyCurrentViewCount - spotifyInitialViewCount;

      youtubeStatCell.textContent = youtubeWeeklyViewCount.toLocaleString();
      spotifyStatCell.textContent = spotifyWeeklyViewCount.toLocaleString();
      break;

    default:
      console.error("Unknown view count type:", viewCountType);
      return;
  }

  row.appendChild(youtubeStatCell);
  row.appendChild(spotifyStatCell);
}

function createSmallPlaylistTableRow(track) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  rankCell.textContent = track.rank || "";

  const coverCell = document.createElement("td");
  coverCell.className = "cover";
  const albumCover = document.createElement("img");
  albumCover.className = "album-cover";
  albumCover.src = track.album_cover_url || "";
  albumCover.alt = "Album Cover";
  coverCell.appendChild(albumCover);

  const trackInfoCell = document.createElement("td");
  trackInfoCell.className = "info";
  const trackInfoDiv = document.createElement("div");
  trackInfoDiv.className = "track-info-div";

  const trackTitle = document.createElement("a");
  trackTitle.className = "track-title";
  trackTitle.href = track.track_url || "#";
  trackTitle.textContent = track.track_name || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artist_name || "Unknown Artist";

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement("br"));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  const externalLinksCell = document.createElement("td");
  externalLinksCell.className = "external";
  if (track.youtube_url) {
    const youtubeLink = createSourceLink("YouTube", track.youtube_url);
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
  const allSources = {
    ...track.additional_sources,
    [track.source_name]: track.track_url,
  };
  Object.keys(allSources).forEach(source => {
    const sourceLink = allSources[source];
    const linkElement = createSourceLink(source, sourceLink);
    sourcesContainer.appendChild(linkElement);
  });
  cell.appendChild(sourcesContainer);
}

function createSourceLink(source, sourceLink) {
  if (!sourceLink) {
    console.warn(`No Link available for source: ${source}`);
    return document.createTextNode("");
  }

  const sourceIcon = document.createElement("img");
  const linkElement = document.createElement("a");
  linkElement.href = sourceLink;
  linkElement.target = "_blank";
  sourceIcon.className = "source-icon";
  switch (source) {
    case "SoundCloud":
      sourceIcon.src = "images/soundcloud_logo.png";
      sourceIcon.alt = "SoundCloud";
      break;
    case "Spotify":
      sourceIcon.src = "images/spotify_logo.png";
      sourceIcon.alt = "Spotify";
      break;
    case "AppleMusic":
      sourceIcon.src = "images/apple_music_logo.png";
      sourceIcon.alt = "Apple Music";
      break;
    case "YouTube":
      sourceIcon.src = "images/youtube_logo.png";
      sourceIcon.alt = "YouTube";
      break;
    default:
      return document.createTextNode("");
  }
  linkElement.appendChild(sourceIcon);
  return linkElement;
}

let playlistData = [];

export function sortTable(column, order, viewCountType) {
  const sortedData = playlistData.map(playlist => {
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

  displayData(sortedData, "main-playlist-data-placeholder", true, viewCountType);
}

function getViewCount(track, platform, viewCountType) {
  const currentCount = track.view_count_data_json?.[platform]?.current_count_json?.current_view_count || 0;
  const initialCount = track.view_count_data_json?.[platform]?.initial_count_json?.initial_view_count || 0;

  if (viewCountType === "total-view-count") {
    return currentCount;
  } else if (viewCountType === "weekly-view-count") {
    return currentCount - initialCount;
  } else {
    console.error("Unknown view count type:", viewCountType);
    return 0;
  }
}

export function resetCollapseStates() {
  document.querySelectorAll(".playlist-content").forEach(content => {
    content.classList.remove("collapsed");
  });
  document.querySelectorAll(".collapse-button").forEach(button => {
    button.textContent = "▼";
  });
}

export function addToggleEventListeners() {
  document.querySelectorAll(".collapse-button").forEach(button => {
    button.removeEventListener("click", toggleCollapse);
  });

  document.querySelectorAll(".collapse-button").forEach(button => {
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
