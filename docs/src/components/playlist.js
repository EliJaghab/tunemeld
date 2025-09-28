import { DJANGO_API_BASE_URL } from "@/config/config.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";
import { graphqlClient } from "@/services/graphql-client.js";
import {
  SERVICE_NAMES,
  TUNEMELD_RANK_FIELD,
  PLAYLIST_PLACEHOLDERS,
} from "@/config/constants.js";

let playCountLookupMap = {};

function getPlayCountForTrack(isrc) {
  return playCountLookupMap[isrc] || {};
}

export async function populatePlayCountMap(isrcs) {
  if (!isrcs || isrcs.length === 0) return;

  try {
    const response = await graphqlClient.getPlayCountsForTracks(isrcs);
    const playCountData = response.tracksPlayCounts || [];

    playCountLookupMap = {};
    playCountData.forEach((data) => {
      if (data && data.isrc) {
        playCountLookupMap[data.isrc] = data;
      }
    });
  } catch (error) {
    console.error("Error fetching play count data:", error);
    playCountLookupMap = {};
  }
}

export async function updateMainPlaylist(genre) {
  try {
    const response = await graphqlClient.getPlaylistTracks(
      genre,
      SERVICE_NAMES.TUNEMELD,
    );
    const data = [response.playlist];
    playlistData = data;

    // Extract ISRCs from TuneMeld playlist tracks and populate play count map
    const isrcs = data.flatMap((playlist) =>
      playlist.tracks.map((track) => track.isrc),
    );
    await populatePlayCountMap(isrcs);

    renderPlaylistTracks(
      data,
      PLAYLIST_PLACEHOLDERS.MAIN,
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
      renderPlaylistTracks(
        data,
        `${service}${PLAYLIST_PLACEHOLDERS.SERVICE_SUFFIX}`,
        null,
        service,
      );
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
  // Always prioritize YouTube first, then fallback to original service
  const youtubeUrl = track.youtubeUrl;

  switch (serviceName) {
    case SERVICE_NAMES.SPOTIFY:
      return youtubeUrl || track.spotifyUrl;
    case SERVICE_NAMES.APPLE_MUSIC:
      return youtubeUrl || track.appleMusicUrl;
    case SERVICE_NAMES.SOUNDCLOUD:
      return youtubeUrl || track.soundcloudUrl;
    case SERVICE_NAMES.YOUTUBE:
      return track.youtubeUrl;
    case SERVICE_NAMES.TUNEMELD:
      return (
        youtubeUrl ||
        track.spotifyUrl ||
        track.appleMusicUrl ||
        track.soundcloudUrl
      );
    default:
      return youtubeUrl;
  }
}

function createTuneMeldPlaylistTableRow(track) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);
  row.setAttribute("data-track", JSON.stringify(track));

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

  const spacerCell = document.createElement("td");
  spacerCell.className = "spacer";

  const seenOnCell = document.createElement("td");
  seenOnCell.className = "seen-on";
  displaySources(seenOnCell, track);

  const externalLinksCell = document.createElement("td");
  externalLinksCell.className = "external";

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);
  row.appendChild(spacerCell);

  // Only show play counts if we're not in TuneMeld rank mode
  const currentColumn = stateManager.getCurrentColumn();
  if (currentColumn !== TUNEMELD_RANK_FIELD) {
    displayPlayCounts(track, row);
  }

  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function createPlayCountElement(
  playCount,
  source,
  url = null,
  percentage = null,
) {
  const container = document.createElement("div");
  container.className = "play-count-container";

  const text = document.createElement("span");
  text.textContent =
    typeof playCount === "string" ? playCount : playCount.toLocaleString();

  container.appendChild(text);

  if (percentage && percentage !== "0") {
    const percentageSpan = document.createElement("span");
    percentageSpan.textContent = ` ${percentage}%`;
    percentageSpan.className = "play-count-percentage";

    if (percentage.startsWith("-")) {
      percentageSpan.classList.add("negative");
    } else if (percentage !== "0") {
      percentageSpan.classList.add("positive");
    }

    container.appendChild(percentageSpan);
  }

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

function createTotalPlayCountElement(playCount, track) {
  const container = document.createElement("div");
  container.className = "total-play-count-container";

  const text = document.createElement("span");
  text.textContent =
    typeof playCount === "string" ? playCount : playCount.toLocaleString();
  text.className = "total-play-count-text";

  container.appendChild(text);
  return container;
}

function createTrendingElement(percentage) {
  const container = document.createElement("div");
  container.className = "trending-container";

  const text = document.createElement("span");
  text.textContent = percentage;
  text.className = "trending-percentage";

  if (percentage.startsWith("-")) {
    text.classList.add("negative");
  } else if (percentage !== "0%" && percentage !== "+0%") {
    text.classList.add("positive");
  }

  container.appendChild(text);
  return container;
}

function displayPlayCounts(track, row) {
  const totalPlaysCell = document.createElement("td");
  totalPlaysCell.className = "total-play-count";

  const trendingCell = document.createElement("td");
  trendingCell.className = "trending";

  const playCountData = getPlayCountForTrack(track.isrc);
  const totalCurrentPlayCount = playCountData.totalCurrentPlayCount;
  const totalCurrentPlayCountAbbreviated =
    playCountData.totalCurrentPlayCountAbbreviated;
  const totalWeeklyChangePercentageFormatted =
    playCountData.totalWeeklyChangePercentageFormatted;

  if (totalCurrentPlayCount && totalCurrentPlayCountAbbreviated) {
    const element = createTotalPlayCountElement(
      totalCurrentPlayCountAbbreviated,
      track,
    );
    totalPlaysCell.appendChild(element);
  }

  if (totalWeeklyChangePercentageFormatted) {
    const formattedPercentage = totalWeeklyChangePercentageFormatted + "%";
    const element = createTrendingElement(formattedPercentage);
    trendingCell.appendChild(element);
  }

  row.appendChild(totalPlaysCell);
  row.appendChild(trendingCell);
}

function createServicePlaylistTableRow(track, serviceName) {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);
  row.setAttribute("data-track", JSON.stringify(track));

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

  // Use new rank-based approach for showing service icons with badges
  const serviceData = [
    {
      source: track.spotifySource,
      rank: track.spotifyRank,
      seenOn: track.seenOnSpotify,
    },
    {
      source: track.appleMusicSource,
      rank: track.appleMusicRank,
      seenOn: track.seenOnAppleMusic,
    },
    {
      source: track.soundcloudSource,
      rank: track.soundcloudRank,
      seenOn: track.seenOnSoundcloud,
    },
  ].filter(
    (item) => item.source !== null && item.source !== undefined && item.seenOn,
  );

  serviceData.forEach((item) => {
    const linkElement = createSourceLinkFromService(item.source, item.rank);
    sourcesContainer.appendChild(linkElement);
  });

  cell.appendChild(sourcesContainer);
}

function createSourceLinkFromService(source, rank = null) {
  if (!source.url) {
    return document.createTextNode("");
  }

  const sourceIcon = document.createElement("img");
  const linkElement = document.createElement("a");
  const container = document.createElement("div");

  container.className = "source-icon-container";
  linkElement.href = source.url || "#";
  linkElement.target = "_blank";
  sourceIcon.className = "source-icon";
  sourceIcon.src = source.iconUrl || "";
  sourceIcon.alt = source.displayName;

  linkElement.appendChild(sourceIcon);
  container.appendChild(linkElement);

  // Add rank badge if rank exists
  if (rank !== null && rank !== undefined) {
    const badge = document.createElement("span");
    badge.className = `rank-badge ${
      rank >= 10 ? "double-digit" : "single-digit"
    }`;
    badge.textContent = rank.toString();
    container.appendChild(badge);
  }

  return container;
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
    // For all other sorts (Total Plays, Trending, etc.), assign new positions based on sort
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

function getPlayCount(track, platform) {
  // Get play count data from lookup map
  const playCountData = getPlayCountForTrack(track.isrc);

  if (platform === SERVICE_NAMES.YOUTUBE) {
    return playCountData.youtubeCurrentPlayCount;
  } else if (platform === SERVICE_NAMES.SPOTIFY) {
    return playCountData.spotifyCurrentPlayCount;
  } else if (
    platform === "Total Plays" ||
    platform === SERVICE_NAMES.TOTAL ||
    platform === "total-plays"
  ) {
    return playCountData.totalCurrentPlayCount;
  } else if (platform === "Trending" || platform === "trending") {
    return playCountData.totalWeeklyChangePercentage;
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
