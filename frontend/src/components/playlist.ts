import { stateManager } from "@/state/StateManager";
import { debugLog } from "@/config/config";
import { appRouter } from "@/routing/router";
import { graphqlClient } from "@/services/graphql-client";
import {
  SERVICE_NAMES,
  TUNEMELD_RANK_FIELD,
  PLAYLIST_PLACEHOLDERS,
} from "@/config/constants";
import {
  hideShimmerLoaders,
  markTunemeldTrackShimmerHidden,
  registerPlaylistReveal,
  trackLoadLog,
} from "@/components/shimmer";
import type { Track, Playlist, ServiceSource, ButtonLabel } from "@/types";

async function fetchAndDisplayData(
  url: string,
  placeholderId: string,
  serviceName: string | null,
): Promise<void> {
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

type PlayCountDisplayMode = "total" | "trending" | "both";

const TOTAL_PLAY_IDENTIFIERS = new Set([
  "totalplaycount",
  "totalplays",
  "totalcurrentplaycount",
]);

const TRENDING_IDENTIFIERS = new Set([
  "totalweeklychangepercentage",
  "totalweeklychange",
  "totalweeklychangepercent",
  "trending",
]);

const SOURCE_ICON_HIDDEN_IDENTIFIERS = new Set([
  ...TOTAL_PLAY_IDENTIFIERS,
  ...TRENDING_IDENTIFIERS,
]);

function normalizeIdentifier(value: string | null | undefined): string | null {
  if (!value) return null;
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function matchesIdentifier(
  identifierSet: Set<string>,
  ...values: Array<string | null | undefined>
): boolean {
  return values.some((value) => {
    const normalized = normalizeIdentifier(value);
    return normalized !== null && identifierSet.has(normalized);
  });
}

function getPlayCountDisplayMode(
  sortField: string | null,
): PlayCountDisplayMode {
  const ranks = stateManager.getRanks();
  const matchingRank = ranks.find((rank) => rank.sortField === sortField);

  const additionalValues = matchingRank
    ? [
        matchingRank.sortField,
        matchingRank.name,
        matchingRank.dataField,
        matchingRank.displayName,
      ]
    : [];

  if (matchesIdentifier(TRENDING_IDENTIFIERS, sortField, ...additionalValues)) {
    return "trending";
  }

  if (
    matchesIdentifier(TOTAL_PLAY_IDENTIFIERS, sortField, ...additionalValues)
  ) {
    return "total";
  }

  return "both";
}

function shouldHideSourceIcons(sortField: string | null): boolean {
  return getPlayCountDisplayMode(sortField) !== "both";
}

function waitForImageElements(images: HTMLImageElement[]): Promise<void> {
  if (images.length === 0) {
    return Promise.resolve();
  }

  const imagePromises = images.map((image) => {
    if (image.complete && image.naturalWidth > 0) {
      return Promise.resolve();
    }

    return new Promise<void>((resolve) => {
      const cleanup = (): void => {
        image.removeEventListener("load", onLoad);
        image.removeEventListener("error", onError);
        resolve();
      };

      const onLoad = (): void => cleanup();
      const onError = (): void => cleanup();

      image.addEventListener("load", onLoad, { once: true });
      image.addEventListener("error", onError, { once: true });
    });
  });

  return Promise.allSettled(imagePromises).then(() => undefined);
}

const playlistDebug = (message: string, meta?: unknown) => {
  debugLog("Playlist", message, meta);
};

export function renderPlaylistTracks(
  playlists: Playlist[],
  placeholderId: string,
  serviceName: string | null,
  serviceDisplayName: string | null = null,
  options: { forceRender?: boolean } = {},
): void {
  const { forceRender = false } = options;
  const isTuneMeldPlaylist = serviceName === SERVICE_NAMES.TUNEMELD;
  const isInitialLoad = stateManager.isInitialLoad();
  const playlistShimmerActive = stateManager.getShimmerState("playlist");
  playlistDebug("renderPlaylistTracks:start", {
    placeholderId,
    serviceName,
    playlistCount: playlists.length,
    forceRender,
    isInitialLoad,
    shouldKeepSkeletonPotential: isTuneMeldPlaylist && isInitialLoad,
  });

  const placeholder = document.getElementById(placeholderId);
  if (!placeholder) {
    console.error(`Placeholder with ID ${placeholderId} not found.`);
    return;
  }

  const renderToken = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  placeholder.dataset.renderToken = renderToken;

  const shouldKeepSkeleton =
    isTuneMeldPlaylist && playlistShimmerActive && !forceRender;

  if (!shouldKeepSkeleton) {
    if (isTuneMeldPlaylist) {
      markTunemeldTrackShimmerHidden({
        reason: forceRender ? "force-render-clear" : "pre-render-clear",
        placeholderChildren: placeholder.childElementCount,
      });
    }
    placeholder.innerHTML = "";
    placeholder.setAttribute("data-rendered", "true");
  } else {
    placeholder.setAttribute("data-rendered", "false");
    // Don't return - continue rendering tracks so they're ready when shimmer fades
  }

  const tableElement = placeholder.closest<HTMLTableElement>("table");
  const dataContainerId = `${placeholderId}--data`;
  let dataContainer = document.getElementById(
    dataContainerId,
  ) as HTMLTableSectionElement | null;
  if (!dataContainer) {
    dataContainer = document.createElement("tbody");
    dataContainer.id = dataContainerId;
    dataContainer.className = "playlist-data";
    placeholder.parentElement?.insertBefore(
      dataContainer,
      placeholder.nextSibling,
    );
  }

  const hasExistingContent = dataContainer.childElementCount > 0;

  const revealDataContainer = (newFragment: DocumentFragment) => {
    dataContainer.innerHTML = "";
    dataContainer.appendChild(newFragment);
    dataContainer.classList.add("playlist-data-hidden");

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (isTuneMeldPlaylist) {
          hideShimmerLoaders();
        }

        dataContainer?.classList.remove("playlist-data-hidden");
      });
    });
  };

  const currentSortField = stateManager.getCurrentColumn();
  const playCountMode = getPlayCountDisplayMode(currentSortField);
  const hideSourceIcons = shouldHideSourceIcons(currentSortField);

  if (tableElement) {
    tableElement.classList.remove(
      "hide-source-icons",
      "playcount-total-only",
      "playcount-trending-only",
    );

    if (isTuneMeldPlaylist) {
      if (hideSourceIcons) {
        tableElement.classList.add("hide-source-icons");
      }
      if (playCountMode === "total") {
        tableElement.classList.add("playcount-total-only");
      } else if (playCountMode === "trending") {
        tableElement.classList.add("playcount-trending-only");
      }
    }

    playlistDebug("renderPlaylistTracks:table state", {
      isTuneMeldPlaylist,
      playCountMode,
      hideSourceIcons,
      classList: tableElement.className,
    });
  }

  const fragment = document.createDocumentFragment();

  playlists.forEach((playlist: Playlist) => {
    playlist.tracks?.forEach((track: Track, index: number) => {
      const currentSortColumn = stateManager.getCurrentColumn();
      const isShowingTuneMeldRanks = currentSortColumn === TUNEMELD_RANK_FIELD;
      const displayRank =
        !isTuneMeldPlaylist || !isShowingTuneMeldRanks ? index + 1 : undefined;

      const row = isTuneMeldPlaylist
        ? createTuneMeldPlaylistTableRow(track, displayRank, playCountMode)
        : createServicePlaylistTableRow(
            track,
            serviceName || "",
            index + 1,
            playCountMode,
          );
      playlistDebug("renderPlaylistTracks:row", {
        isrc: track.isrc,
        trackName: track.trackName,
        isTuneMeldPlaylist,
        index,
        playCountMode,
      });
      fragment.appendChild(row);
    });
  });

  if (isTuneMeldPlaylist) {
    const tempContainer = document.createElement("div");
    tempContainer.appendChild(fragment.cloneNode(true) as DocumentFragment);
    const albumImages = Array.from(
      tempContainer.querySelectorAll<HTMLImageElement>("img.album-cover"),
    );
    const imagesPromise = waitForImageElements(albumImages);
    registerPlaylistReveal(imagesPromise);

    imagesPromise.finally(() => {
      if (placeholder.dataset.renderToken !== renderToken) {
        playlistDebug(
          "renderPlaylistTracks: imagesPromise stale token, skipping reveal",
        );
        return;
      }

      if (tableElement) {
        tableElement.classList.remove("tracks-hidden");
        tableElement.classList.remove(
          "hide-source-icons",
          "playcount-total-only",
          "playcount-trending-only",
        );
        if (hideSourceIcons) {
          tableElement.classList.add("hide-source-icons");
        }
        if (playCountMode === "total") {
          tableElement.classList.add("playcount-total-only");
        } else if (playCountMode === "trending") {
          tableElement.classList.add("playcount-trending-only");
        }

        playlistDebug("renderPlaylistTracks: reveal table", {
          playCountMode,
          classList: tableElement.className,
        });
      }

      markTunemeldTrackShimmerHidden({ reason: "tracks-ready" });

      placeholder.setAttribute("data-rendered", "true");

      trackLoadLog("Tunemeld tracks rendered", {
        trackCount: dataContainer.childElementCount,
        playCountMode,
      });

      revealDataContainer(fragment);

      stateManager.markLoaded("tracksLoaded");
      stateManager.markLoaded("playlistDataLoaded");

      setTimeout(() => {
        if (placeholder.dataset.renderToken === renderToken) {
          placeholder.innerHTML = "";
        }
      }, 550);
    });
  } else {
    placeholder.innerHTML = "";
    placeholder.setAttribute("data-rendered", "true");
    stateManager.markLoaded("serviceDataLoaded");
    stateManager.markLoaded("tracksLoaded");
    revealDataContainer(fragment);
  }

  playlistDebug("renderPlaylistTracks:end", {
    placeholderId,
    serviceName,
    isTuneMeldPlaylist,
    playCountMode,
  });
}

function setTrackInfoLabels(
  trackTitle: HTMLAnchorElement,
  artistElement: HTMLSpanElement,
  track: Track,
  serviceName: string,
): void {
  const fullTrackName =
    track.fullTrackName || track.trackName || "Unknown Track";
  const fullArtistName =
    track.fullArtistName || track.artistName || "Unknown Artist";

  // Use button labels already included in track data
  if (track.buttonLabels && track.buttonLabels.length > 0) {
    const trackLabel = track.buttonLabels.find(
      (label: ButtonLabel) => label.buttonType === "track_title",
    );

    if (trackLabel) {
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
  }

  // Set artist tooltip
  artistElement.title = fullArtistName;
  artistElement.setAttribute("aria-label", `Artist: ${fullArtistName}`);
}

function createTuneMeldPlaylistTableRow(
  track: Track,
  displayRank: number | undefined,
  playCountMode: PlayCountDisplayMode,
): HTMLTableRowElement {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);
  row.setAttribute("data-track", JSON.stringify(track));

  const rankCell = document.createElement("td");
  rankCell.className = "rank";
  // Show current position if displayRank provided, otherwise show original tunemeldRank
  const currentSortColumn = stateManager.getCurrentColumn();
  const showDisplayRank =
    displayRank !== undefined && currentSortColumn !== TUNEMELD_RANK_FIELD;
  rankCell.textContent = showDisplayRank
    ? displayRank.toString()
    : track.tunemeldRank?.toString() || "-";

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
  // For TuneMeld Playlist, use the first available actual service URL (YouTube priority)
  const trackUrl =
    track.youtubeSource?.url ||
    track.spotifySource?.url ||
    track.appleMusicSource?.url ||
    track.soundcloudSource?.url ||
    "#";
  trackTitle.href = trackUrl;
  trackTitle.textContent = track.trackName || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artistName || "Unknown Artist";

  // Set backend-driven labels
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
  const currentRankColumn = stateManager.getCurrentColumn();
  if (currentRankColumn !== TUNEMELD_RANK_FIELD) {
    displayPlayCounts(track, row, playCountMode);
  }

  row.appendChild(seenOnCell);
  row.appendChild(externalLinksCell);

  return row;
}

function createTotalPlayCountElement(
  playCount: number | string,
  track: Track,
): HTMLElement {
  const container = document.createElement("div");
  container.className = "total-play-count-container";

  const text = document.createElement("span");
  text.textContent =
    typeof playCount === "string" ? playCount : playCount.toLocaleString();
  text.className = "total-play-count-text";

  container.appendChild(text);
  return container;
}

function createTrendingElement(percentage: string): HTMLElement {
  const container = document.createElement("div");
  container.className = "trending-container";

  const text = document.createElement("span");
  text.textContent = percentage;
  text.className = "trending-percentage";

  const numericValue = parseFloat(percentage.replace(/[^0-9.-]+/g, ""));
  if (!Number.isNaN(numericValue)) {
    if (numericValue < 0) {
      text.classList.add("negative");
    } else if (numericValue > 0) {
      text.classList.add("positive");
    }
  }

  container.appendChild(text);
  return container;
}

function formatAbbreviatedPlayCount(count: number): string {
  const abs = Math.abs(count);
  if (abs >= 1_000_000_000) {
    return `${(count / 1_000_000_000).toFixed(1)}B`;
  }
  if (abs >= 1_000_000) {
    return `${(count / 1_000_000).toFixed(1)}M`;
  }
  if (abs >= 1_000) {
    return `${(count / 1_000).toFixed(1)}K`;
  }
  return count.toLocaleString();
}

function getPlayCountForTrack(track: Track) {
  const countValue = track.totalCurrentPlayCount;
  const percentageValue = track.totalWeeklyChangePercentage;

  const parsedCount =
    typeof countValue === "string"
      ? Number(countValue)
      : typeof countValue === "number"
      ? countValue
      : null;

  let abbreviated: string | null = null;
  if (typeof parsedCount === "number" && !Number.isNaN(parsedCount)) {
    abbreviated = formatAbbreviatedPlayCount(parsedCount);
  }

  const parsedPercentage =
    typeof percentageValue === "string"
      ? Number(percentageValue)
      : typeof percentageValue === "number"
      ? percentageValue
      : null;

  let percentageFormatted: string | null = null;
  if (typeof parsedPercentage === "number" && !Number.isNaN(parsedPercentage)) {
    const rounded = Math.round(parsedPercentage * 10) / 10;
    let formattedNumber = rounded.toFixed(1);
    if (formattedNumber.endsWith(".0")) {
      formattedNumber = formattedNumber.slice(0, -2);
    }
    const sign = rounded > 0 ? "+" : "";
    percentageFormatted = `${sign}${formattedNumber}%`;
  }

  playlistDebug("getPlayCountForTrack", {
    isrc: track.isrc,
    trackName: track.trackName,
    rawTotalCurrentPlayCount: countValue,
    parsedTotalCurrentPlayCount: parsedCount,
    formattedTotalCurrentPlayCount: abbreviated,
    rawWeeklyChange: percentageValue,
    parsedWeeklyChange: parsedPercentage,
    formattedWeeklyChange: percentageFormatted,
  });

  return {
    totalCurrentPlayCount: parsedCount ?? null,
    totalCurrentPlayCountAbbreviated: abbreviated,
    totalWeeklyChangePercentage: parsedPercentage ?? null,
    totalWeeklyChangePercentageFormatted: percentageFormatted,
    youtubeCurrentPlayCount: track.youtubeCurrentPlayCount,
    spotifyCurrentPlayCount: track.spotifyCurrentPlayCount,
  };
}

function displayPlayCounts(
  track: Track,
  row: HTMLTableRowElement,
  mode: PlayCountDisplayMode,
): void {
  const showTotal = mode !== "trending";
  const showTrending = mode !== "total";

  const totalPlaysCell = document.createElement("td");
  totalPlaysCell.className = "total-play-count";

  const trendingCell = document.createElement("td");
  trendingCell.className = "trending";

  const playCountData = getPlayCountForTrack(track);
  const totalCurrentPlayCountAbbreviated =
    playCountData.totalCurrentPlayCountAbbreviated;
  const totalWeeklyChangePercentageFormatted =
    playCountData.totalWeeklyChangePercentageFormatted;

  if (showTotal && totalCurrentPlayCountAbbreviated !== null) {
    const element = createTotalPlayCountElement(
      totalCurrentPlayCountAbbreviated,
      track,
    );
    totalPlaysCell.appendChild(element);
  } else if (!showTotal) {
    totalPlaysCell.classList.add("playcount-hidden");
  }

  if (showTrending && totalWeeklyChangePercentageFormatted) {
    const element = createTrendingElement(totalWeeklyChangePercentageFormatted);
    trendingCell.appendChild(element);
  } else if (!showTrending) {
    trendingCell.classList.add("playcount-hidden");
  }

  playlistDebug("displayPlayCounts", {
    isrc: track.isrc,
    mode,
    showTotal,
    showTrending,
    totalValue: totalCurrentPlayCountAbbreviated,
    trendingValue: totalWeeklyChangePercentageFormatted,
  });

  row.appendChild(totalPlaysCell);
  row.appendChild(trendingCell);
}

function createServicePlaylistTableRow(
  track: Track,
  serviceName: string,
  displayRank?: number,
  playCountMode: PlayCountDisplayMode = "both",
): HTMLTableRowElement {
  const row = document.createElement("tr");

  row.setAttribute("data-isrc", track.isrc);
  row.setAttribute("data-track", JSON.stringify(track));

  const rankCell = document.createElement("td");
  rankCell.className = "rank";

  // Determine which rank to display based on service
  let serviceRank: number | null | undefined = null;
  if (serviceName === SERVICE_NAMES.SPOTIFY) {
    serviceRank = track.spotifyRank;
  } else if (serviceName === SERVICE_NAMES.APPLE_MUSIC) {
    serviceRank = track.appleMusicRank;
  } else if (serviceName === SERVICE_NAMES.SOUNDCLOUD) {
    serviceRank = track.soundcloudRank;
  }

  rankCell.textContent = serviceRank?.toString() || "";

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
  // For service playlists, use the specific service's actual URL
  let trackUrl = "#";
  if (serviceName === SERVICE_NAMES.SPOTIFY) {
    trackUrl = track.spotifySource?.url || "#";
  } else if (serviceName === SERVICE_NAMES.APPLE_MUSIC) {
    trackUrl = track.appleMusicSource?.url || "#";
  } else if (serviceName === SERVICE_NAMES.SOUNDCLOUD) {
    trackUrl = track.soundcloudSource?.url || "#";
  } else if (serviceName === SERVICE_NAMES.YOUTUBE) {
    trackUrl = track.youtubeSource?.url || "#";
  } else if (serviceName === SERVICE_NAMES.TOTAL) {
    // For total views, use first available actual URL
    trackUrl =
      track.youtubeSource?.url ||
      track.spotifySource?.url ||
      track.appleMusicSource?.url ||
      track.soundcloudSource?.url ||
      "#";
  }
  trackTitle.href = trackUrl;
  trackTitle.textContent = track.trackName || "Unknown Track";

  const artistNameElement = document.createElement("span");
  artistNameElement.className = "artist-name";
  artistNameElement.textContent = track.artistName || "Unknown Artist";

  // Set backend-driven labels
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
    // Add spacer column to match TOTAL_PLAYS table structure
    const spacerCell = document.createElement("td");
    spacerCell.className = "spacer";
    row.appendChild(spacerCell);

    // Add play count columns
    displayPlayCounts(track, row, playCountMode);

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

function displaySources(cell: HTMLTableCellElement, track: Track): void {
  if (shouldHideSourceIcons(stateManager.getCurrentColumn())) {
    return;
  }

  const sourcesContainer = document.createElement("div");
  sourcesContainer.className = "track-sources";

  // Show service icons when tracks have ranks for those services
  const serviceData = [
    {
      source: track.spotifySource,
      rank: track.spotifyRank,
    },
    {
      source: track.appleMusicSource,
      rank: track.appleMusicRank,
    },
    {
      source: track.soundcloudSource,
      rank: track.soundcloudRank,
    },
  ].filter((item) => {
    // Only show service icons when the track has a rank for that service
    return item.rank !== null && item.rank !== undefined;
  });

  serviceData.forEach((item) => {
    if (item.source) {
      const linkElement = createSourceLinkFromService(
        item.source,
        item.rank,
        track,
      );
      sourcesContainer.appendChild(linkElement);
    }
  });

  cell.appendChild(sourcesContainer);
}

function createSourceLinkFromService(
  source: ServiceSource,
  rank: number | null = null,
  trackData: Track | null = null,
): HTMLElement {
  if (!source.url) {
    const textNode = document.createTextNode("");
    const span = document.createElement("span");
    span.appendChild(textNode);
    return span;
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
      (label: ButtonLabel) =>
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

let playlistData: Playlist[] = [];

export function setPlaylistData(data: Playlist[]): void {
  playlistData = data;
}

export function sortTable(column: string, order: string): void {
  const ranks = appRouter.getAvailableRanks();
  const rankConfig = ranks.find((rank) => rank.sortField === column);

  if (!rankConfig) {
    console.error(`Unknown sort column: ${column}`);
    return;
  }

  const sortedData = playlistData.map((playlist: Playlist) => {
    playlist.tracks?.sort((a, b) => {
      let aValue = (a as any)[rankConfig.dataField] as number;
      let bValue = (b as any)[rankConfig.dataField] as number;

      if (aValue == null) aValue = 0;
      if (bValue == null) bValue = 0;

      return order === "asc" ? aValue - bValue : bValue - aValue;
    });

    // Note: tunemeldRank should NEVER be modified as it preserves backend-computed positions
    // Rank display numbers are handled in renderPlaylistTracks based on current sort order

    return playlist;
  });

  // Update the module-level data so subsequent operations work correctly
  playlistData = sortedData;

  // Only render if not initial load (shimmer is showing)
  if (!stateManager.isInitialLoad()) {
    renderPlaylistTracks(
      sortedData,
      "main-playlist-data-placeholder",
      SERVICE_NAMES.TUNEMELD,
      null,
      { forceRender: true },
    );
  }
}

function getPlayCount(track: Track, platform: string): number | null {
  // Get play count data from lookup map
  const playCountData = getPlayCountForTrack(track);

  if (platform === SERVICE_NAMES.YOUTUBE) {
    return playCountData.youtubeCurrentPlayCount ?? null;
  } else if (platform === SERVICE_NAMES.SPOTIFY) {
    return playCountData.spotifyCurrentPlayCount ?? null;
  } else if (
    platform === "Total Plays" ||
    platform === SERVICE_NAMES.TOTAL ||
    platform === "total-plays"
  ) {
    return playCountData.totalCurrentPlayCount ?? null;
  } else if (platform === "Trending" || platform === "trending") {
    return playCountData.totalWeeklyChangePercentage ?? null;
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
      async (button: Element) => {
        const targetId = button.getAttribute("data-target");
        const content = targetId
          ? document.querySelector(`${targetId} .playlist-content`)
          : null;
        const isCollapsed = content?.classList.contains("collapsed") || false;
        if (targetId) {
          await updateCollapseButtonLabels(
            button as HTMLElement,
            targetId,
            isCollapsed,
          );
        }
      },
    ),
  );
}

async function toggleCollapse(event: Event): Promise<void> {
  const button = event.currentTarget as HTMLElement;
  const targetId = button?.getAttribute("data-target");
  const content = targetId
    ? document.querySelector(`${targetId} .playlist-content`)
    : null;
  const playlist = targetId ? document.querySelector(targetId) : null;

  if (content) {
    content.classList.toggle("collapsed");
  }
  if (playlist) {
    playlist.classList.toggle("collapsed");
  }

  const isCollapsed = content?.classList.contains("collapsed") || false;
  if (button) {
    button.textContent = isCollapsed ? "▲" : "▼";
  }

  if (button && targetId) {
    await updateCollapseButtonLabels(button, targetId, isCollapsed);
  }
}

async function updateCollapseButtonLabels(
  button: HTMLElement,
  targetId: string,
  isCollapsed: boolean,
): Promise<void> {
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
    // Skip individual button label requests for performance
    const buttonLabels: ButtonLabel[] = [];

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
