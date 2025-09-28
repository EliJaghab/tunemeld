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

function enrichTracksWithPlayCountData(tracks) {
  tracks.forEach((track) => {
    const playCountData = playCountLookupMap[track.isrc];
    if (playCountData) {
      // Add play count fields directly to track object for sorting
      track.totalCurrentPlayCount = playCountData.totalCurrentPlayCount || 0;
      track.totalWeeklyChangePercentage =
        playCountData.totalWeeklyChangePercentage || 0;
      track.spotifyCurrentPlayCount =
        playCountData.spotifyCurrentPlayCount || 0;
      track.youtubeCurrentPlayCount =
        playCountData.youtubeCurrentPlayCount || 0;
    }
  });
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

    // Enrich track objects with play count data for sorting
    data.forEach((playlist) => {
      enrichTracksWithPlayCountData(playlist.tracks);
    });

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

      // Populate play count data for total views and other services that need it
      if (service === SERVICE_NAMES.TOTAL || data[0]?.tracks?.length > 0) {
        const isrcs = data.flatMap((playlist) =>
          playlist.tracks.map((track) => track.isrc),
        );
        await populatePlayCountMap(isrcs);

        // Enrich track objects with play count data for sorting
        data.forEach((playlist) => {
          enrichTracksWithPlayCountData(playlist.tracks);
        });
      }

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

async function setTrackInfoLabels(
  trackTitle,
  artistElement,
  track,
  serviceName,
) {
  try {
    const fullTrackName =
      track.fullTrackName || track.trackName || "Unknown Track";
    const fullArtistName =
      track.fullArtistName || track.artistName || "Unknown Artist";

    // Get backend-driven button labels for track title
    const trackButtonLabels = await graphqlClient.getMiscButtonLabels(
      "track_title",
      serviceName,
    );

    if (trackButtonLabels && trackButtonLabels.length > 0) {
      const trackLabel = trackButtonLabels[0];
      if (trackLabel.title) {
        // Replace placeholders with actual track info
        trackTitle.title = trackLabel.title
          .replace("{trackName}", fullTrackName)
          .replace("{artistName}", fullArtistName);
      }
      if (trackLabel.ariaLabel) {
        trackTitle.setAttribute(
          "aria-label",
          trackLabel.ariaLabel
            .replace("{trackName}", fullTrackName)
            .replace("{artistName}", fullArtistName),
        );
      }
    }

    // Set artist tooltip
    artistElement.title = fullArtistName;
    artistElement.setAttribute("aria-label", `Artist: ${fullArtistName}`);
  } catch (error) {
    console.warn("Failed to load track info labels:", error);
    // Continue without labels if fetch fails
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
  // For TuneMeld Playlist, use the first available internal track URL (YouTube priority)
  const trackUrl =
    track.trackDetailUrlYoutube ||
    track.trackDetailUrlSpotify ||
    track.trackDetailUrlAppleMusic ||
    track.trackDetailUrlSoundcloud ||
    "#";
  trackTitle.href = trackUrl;
  trackTitle.textContent = track.trackName || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artistName || "Unknown Artist";

  // Set backend-driven labels asynchronously
  setTrackInfoLabels(
    trackTitle,
    artistNameElement,
    track,
    SERVICE_NAMES.TUNEMELD,
  );

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
  // For service playlists, use the specific service's internal track URL
  let trackUrl = "#";
  if (serviceName === SERVICE_NAMES.SPOTIFY) {
    trackUrl = track.trackDetailUrlSpotify || "#";
  } else if (serviceName === SERVICE_NAMES.APPLE_MUSIC) {
    trackUrl = track.trackDetailUrlAppleMusic || "#";
  } else if (serviceName === SERVICE_NAMES.SOUNDCLOUD) {
    trackUrl = track.trackDetailUrlSoundcloud || "#";
  } else if (serviceName === SERVICE_NAMES.YOUTUBE) {
    trackUrl = track.trackDetailUrlYoutube || "#";
  } else if (serviceName === SERVICE_NAMES.TOTAL) {
    // For total views, use first available internal URL
    trackUrl =
      track.trackDetailUrlYoutube ||
      track.trackDetailUrlSpotify ||
      track.trackDetailUrlAppleMusic ||
      track.trackDetailUrlSoundcloud ||
      "#";
  }
  trackTitle.href = trackUrl;
  trackTitle.textContent = track.trackName || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artistName || "Unknown Artist";

  // Set backend-driven labels asynchronously
  setTrackInfoLabels(trackTitle, artistNameElement, track, serviceName);

  trackInfoDiv.appendChild(trackTitle);
  trackInfoDiv.appendChild(document.createElement("br"));
  trackInfoDiv.appendChild(artistNameElement);

  trackInfoCell.appendChild(trackInfoDiv);

  row.appendChild(rankCell);
  row.appendChild(coverCell);
  row.appendChild(trackInfoCell);

  // Check if this is the total views page - if so, show play counts instead of just external links
  if (serviceName === SERVICE_NAMES.TOTAL) {
    // Add spacer column to match PLAYCOUNT table structure
    const spacerCell = document.createElement("td");
    spacerCell.className = "spacer";
    row.appendChild(spacerCell);

    // Add play count columns
    displayPlayCounts(track, row);

    // Add seen-on column (service icons)
    const seenOnCell = document.createElement("td");
    seenOnCell.className = "seen-on";
    displaySources(seenOnCell, track);
    row.appendChild(seenOnCell);

    // Add external links column
    const externalLinksCell = document.createElement("td");
    externalLinksCell.className = "external";
    if (track.youtubeSource) {
      const youtubeLink = createSourceLinkFromService(
        track.youtubeSource,
        null,
        track,
      );
      externalLinksCell.appendChild(youtubeLink);
    }
    row.appendChild(externalLinksCell);
  } else {
    // Regular service playlist - just show external links
    const externalLinksCell = document.createElement("td");
    externalLinksCell.className = "external";
    if (track.youtubeSource) {
      const youtubeLink = createSourceLinkFromService(
        track.youtubeSource,
        null,
        track,
      );
      externalLinksCell.appendChild(youtubeLink);
    }
    row.appendChild(externalLinksCell);
  }

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
    const linkElement = createSourceLinkFromService(
      item.source,
      item.rank,
      track,
    );
    sourcesContainer.appendChild(linkElement);
  });

  cell.appendChild(sourcesContainer);
}

function createSourceLinkFromService(source, rank = null, trackData = null) {
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

  // Add full track name and service context to tooltip
  if (trackData && trackData.buttonLabels) {
    // Look for source icon button label that matches this service
    const sourceLabel = trackData.buttonLabels.find(
      (label) =>
        label.buttonType === "source_icon" && label.context === source.name,
    );
    if (sourceLabel) {
      if (sourceLabel.title) {
        linkElement.title = sourceLabel.title;
      }
      if (sourceLabel.ariaLabel) {
        linkElement.setAttribute("aria-label", sourceLabel.ariaLabel);
      }
    }
  } else if (trackData) {
    // Fallback: create basic tooltip with full track name
    const fullTrackName =
      trackData.fullTrackName || trackData.trackName || "Unknown Track";
    const fullArtistName =
      trackData.fullArtistName || trackData.artistName || "Unknown Artist";
    const rankText = rank ? ` (Rank #${rank})` : "";
    linkElement.title = `Play '${fullTrackName}' by ${fullArtistName} on ${source.displayName}${rankText}`;
    linkElement.setAttribute(
      "aria-label",
      `Play ${fullTrackName} by ${fullArtistName} on ${source.displayName}`,
    );
  }

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

export async function addToggleEventListeners() {
  document.querySelectorAll(".collapse-button").forEach((button) => {
    button.removeEventListener("click", toggleCollapse);
  });

  document.querySelectorAll(".collapse-button").forEach((button) => {
    button.addEventListener("click", toggleCollapse);
  });

  // Add initial labels to all collapse buttons
  await Promise.all(
    Array.from(document.querySelectorAll(".collapse-button")).map(
      async (button) => {
        const targetId = button.getAttribute("data-target");
        const content = document.querySelector(`${targetId} .playlist-content`);
        const isCollapsed = content?.classList.contains("collapsed") || false;
        await updateCollapseButtonLabels(button, targetId, isCollapsed);
      },
    ),
  );
}

async function toggleCollapse(event) {
  const button = event.currentTarget;
  const targetId = button.getAttribute("data-target");
  const content = document.querySelector(`${targetId} .playlist-content`);
  const playlist = document.querySelector(targetId);

  content.classList.toggle("collapsed");
  playlist.classList.toggle("collapsed");

  const isCollapsed = content.classList.contains("collapsed");
  button.textContent = isCollapsed ? "▲" : "▼";

  await updateCollapseButtonLabels(button, targetId, isCollapsed);
}

async function updateCollapseButtonLabels(button, targetId, isCollapsed) {
  try {
    let playlistType = "main";
    if (targetId.includes(SERVICE_NAMES.SPOTIFY)) {
      playlistType = SERVICE_NAMES.SPOTIFY;
    } else if (targetId.includes(SERVICE_NAMES.APPLE_MUSIC)) {
      playlistType = SERVICE_NAMES.APPLE_MUSIC;
    } else if (targetId.includes(SERVICE_NAMES.SOUNDCLOUD)) {
      playlistType = SERVICE_NAMES.SOUNDCLOUD;
    }

    const context = `${playlistType}_${isCollapsed ? "collapsed" : "expanded"}`;
    const buttonLabels = await graphqlClient.getMiscButtonLabels(
      "collapse_button",
      context,
    );

    if (buttonLabels && buttonLabels.length > 0) {
      const collapseLabel = buttonLabels[0];
      if (collapseLabel.title) {
        button.title = collapseLabel.title;
      }
      if (collapseLabel.ariaLabel) {
        button.setAttribute("aria-label", collapseLabel.ariaLabel);
      }
    }
  } catch (error) {
    console.warn("Failed to update collapse button labels:", error);
    // Continue without labels if fetch fails
  }
}
