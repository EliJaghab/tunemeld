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
  sortField: string | null
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
  options: { forceRender?: boolean; showAllTracks?: boolean } = {}
): void {
  const { forceRender = false, showAllTracks = false } = options;
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

  const shouldKeepSkeleton = isTuneMeldPlaylist && playlistShimmerActive;

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
    dataContainerId
  ) as HTMLTableSectionElement | null;
  if (!dataContainer) {
    dataContainer = document.createElement("tbody");
    dataContainer.id = dataContainerId;
    dataContainer.className = "playlist-data";
    placeholder.parentElement?.insertBefore(
      dataContainer,
      placeholder.nextSibling
    );
  }

  const hasExistingContent = dataContainer.childElementCount > 0;

  const revealDataContainer = (newFragment: DocumentFragment) => {
    dataContainer.innerHTML = "";
    dataContainer.appendChild(newFragment);
    dataContainer.style.display = "";
    dataContainer.classList.add("playlist-data-hidden");

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        // Shimmer hiding is handled by updateGenreData in selectors.ts
        // Don't hide here - this gets called during intermediate renders
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
      "playcount-trending-only"
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
  const INITIAL_TRACK_LIMIT = 5;

  playlists.forEach((playlist: Playlist) => {
    const tracks = playlist.tracks || [];
    const isServicePlaylist = !isTuneMeldPlaylist;
    const shouldLimitTracks = isServicePlaylist && !showAllTracks;
    const tracksToRender = shouldLimitTracks
      ? tracks.slice(0, INITIAL_TRACK_LIMIT)
      : tracks;
    const hasMoreTracks =
      shouldLimitTracks && tracks.length > INITIAL_TRACK_LIMIT;

    tracksToRender.forEach((track: Track, index: number) => {
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
            playCountMode
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

    if (hasMoreTracks) {
      const showAllRow = createShowAllTracksRow(
        placeholderId,
        tracks.length,
        serviceName
      );
      fragment.appendChild(showAllRow);
    }
  });

  if (isTuneMeldPlaylist) {
    const tempContainer = document.createElement("div");
    tempContainer.appendChild(fragment.cloneNode(true) as DocumentFragment);
    const albumImages = Array.from(
      tempContainer.querySelectorAll<HTMLImageElement>("img.album-cover")
    );
    const imagesPromise = waitForImageElements(albumImages);
    registerPlaylistReveal(imagesPromise);

    imagesPromise.finally(() => {
      if (placeholder.dataset.renderToken !== renderToken) {
        playlistDebug(
          "renderPlaylistTracks: imagesPromise stale token, skipping reveal"
        );
        return;
      }

      if (tableElement) {
        tableElement.classList.remove("tracks-hidden");
        tableElement.classList.remove(
          "hide-source-icons",
          "playcount-total-only",
          "playcount-trending-only"
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
  serviceName: string
): void {
  const fullTrackName =
    track.fullTrackName || track.trackName || "Unknown Track";
  const fullArtistName =
    track.fullArtistName || track.artistName || "Unknown Artist";

  if (track.buttonLabels && track.buttonLabels.length > 0) {
    const trackLabel = track.buttonLabels.find(
      (label: ButtonLabel) => label.buttonType === "track_title"
    );

    if (trackLabel) {
      if (trackLabel.title) {
        trackTitle.title = trackLabel.title
          .replace("{trackName}", fullTrackName)
          .replace("{artistName}", fullArtistName);
      }
      if (trackLabel.ariaLabel) {
        trackTitle.setAttribute(
          "aria-label",
          trackLabel.ariaLabel
            .replace("{trackName}", fullTrackName)
            .replace("{artistName}", fullArtistName)
        );
      }
    }
  }

  artistElement.title = fullArtistName;
  artistElement.setAttribute("aria-label", `Artist: ${fullArtistName}`);
}

function getRankValue(
  track: Track,
  serviceName: string,
  displayRank?: number
): string {
  if (serviceName === SERVICE_NAMES.TUNEMELD) {
    const currentSortColumn = stateManager.getCurrentColumn();
    const showDisplayRank =
      displayRank !== undefined && currentSortColumn !== TUNEMELD_RANK_FIELD;
    return showDisplayRank
      ? displayRank.toString()
      : track.tunemeldRank?.toString() || "-";
  }

  const rankMap: Record<string, number | null | undefined> = {
    [SERVICE_NAMES.SPOTIFY]: track.spotifyRank,
    [SERVICE_NAMES.APPLE_MUSIC]: track.appleMusicRank,
    [SERVICE_NAMES.SOUNDCLOUD]: track.soundcloudRank,
  };

  return rankMap[serviceName]?.toString() || "";
}

function getTrackUrl(track: Track, serviceName: string): string {
  if (
    serviceName === SERVICE_NAMES.TUNEMELD ||
    serviceName === SERVICE_NAMES.TOTAL
  ) {
    return (
      track.youtubeSource?.url ||
      track.spotifySource?.url ||
      track.appleMusicSource?.url ||
      track.soundcloudSource?.url ||
      "#"
    );
  }

  const urlMap: Record<string, string | undefined> = {
    [SERVICE_NAMES.SPOTIFY]: track.spotifySource?.url,
    [SERVICE_NAMES.APPLE_MUSIC]: track.appleMusicSource?.url,
    [SERVICE_NAMES.SOUNDCLOUD]: track.soundcloudSource?.url,
    [SERVICE_NAMES.YOUTUBE]: track.youtubeSource?.url,
  };

  return urlMap[serviceName] || "#";
}

function getTrackLabels(track: Track): {
  titleAttr: string;
  ariaLabel: string;
  artistTitle: string;
} {
  const fullTrackName =
    track.fullTrackName || track.trackName || "Unknown Track";
  const fullArtistName =
    track.fullArtistName || track.artistName || "Unknown Artist";

  let titleAttr = `${fullTrackName} by ${fullArtistName}`;
  let ariaLabel = `Play ${fullTrackName} by ${fullArtistName}`;

  if (track.buttonLabels && track.buttonLabels.length > 0) {
    const trackLabel = track.buttonLabels.find(
      (label: ButtonLabel) => label.buttonType === "track_title"
    );
    if (trackLabel) {
      if (trackLabel.title) {
        titleAttr = trackLabel.title
          .replace("{trackName}", fullTrackName)
          .replace("{artistName}", fullArtistName);
      }
      if (trackLabel.ariaLabel) {
        ariaLabel = trackLabel.ariaLabel
          .replace("{trackName}", fullTrackName)
          .replace("{artistName}", fullArtistName);
      }
    }
  }

  return {
    titleAttr,
    ariaLabel,
    artistTitle: `Artist: ${fullArtistName}`,
  };
}

function renderCoverCellHtml(track: Track): string {
  return `
    <td class="cover">
      <img class="album-cover"
           src="${track.albumCoverUrl || ""}"
           alt="Album Cover">
    </td>
  `;
}

function renderTrackInfoCellHtml(track: Track, serviceName: string): string {
  const trackUrl = getTrackUrl(track, serviceName);
  const trackName = track.trackName || "Unknown Track";
  const artistName = track.artistName || "Unknown Artist";
  const labels = getTrackLabels(track);

  return `
    <td class="info">
      <div class="track-info-div">
        <a class="track-title"
           href="${trackUrl}"
           title="${labels.titleAttr}"
           aria-label="${labels.ariaLabel}">
          ${trackName}
        </a>
        <br>
        <span class="artist-name"
              title="${labels.artistTitle}">
          ${artistName}
        </span>
      </div>
    </td>
  `;
}

function renderPlayCountCellsHtml(
  track: Track,
  playCountMode: PlayCountDisplayMode
): string {
  const playCountData = getPlayCountForTrack(track);
  const showTotal = playCountMode !== "trending";
  const showTrending = playCountMode !== "total";

  let totalHtml = "";
  let trendingHtml = "";

  if (showTotal && playCountData.totalCurrentPlayCountAbbreviated) {
    totalHtml = `
      <td class="total-play-count">
        <div class="total-play-count-container">
          <span class="total-play-count-text">
            ${playCountData.totalCurrentPlayCountAbbreviated}
          </span>
        </div>
      </td>
    `;
  } else if (!showTotal) {
    totalHtml = '<td class="total-play-count playcount-hidden"></td>';
  }

  if (showTrending && playCountData.totalWeeklyChangePercentageFormatted) {
    const percentage = playCountData.totalWeeklyChangePercentageFormatted;
    const numericValue = parseFloat(percentage.replace(/[^0-9.-]+/g, ""));
    const trendClass =
      numericValue < 0 ? "negative" : numericValue > 0 ? "positive" : "";

    trendingHtml = `
      <td class="trending">
        <div class="trending-container">
          <span class="trending-percentage ${trendClass}">
            ${percentage}
          </span>
        </div>
      </td>
    `;
  } else if (!showTrending) {
    trendingHtml = '<td class="trending playcount-hidden"></td>';
  }

  return totalHtml + trendingHtml;
}

function createTuneMeldPlaylistTableRow(
  track: Track,
  displayRank: number | undefined,
  playCountMode: PlayCountDisplayMode
): HTMLTableRowElement {
  const row = document.createElement("tr");
  row.setAttribute("data-isrc", track.isrc);
  row.setAttribute("data-track", JSON.stringify(track));

  const rankValue = getRankValue(track, SERVICE_NAMES.TUNEMELD, displayRank);
  const currentRankColumn = stateManager.getCurrentColumn();
  const showPlayCounts = currentRankColumn !== TUNEMELD_RANK_FIELD;

  row.innerHTML = `
    <td class="rank">${rankValue}</td>
    ${renderCoverCellHtml(track)}
    ${renderTrackInfoCellHtml(track, SERVICE_NAMES.TUNEMELD)}
    <td class="spacer"></td>
    ${showPlayCounts ? renderPlayCountCellsHtml(track, playCountMode) : ""}
    <td class="seen-on" data-seen-on="${track.isrc}"></td>
    <td class="external"></td>
  `;

  const seenOnCell = row.querySelector(
    `[data-seen-on="${track.isrc}"]`
  ) as HTMLTableCellElement;
  if (seenOnCell) {
    displaySources(seenOnCell, track);
  }

  return row;
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

function createServicePlaylistTableRow(
  track: Track,
  serviceName: string,
  displayRank?: number,
  playCountMode: PlayCountDisplayMode = "both"
): HTMLTableRowElement {
  const row = document.createElement("tr");
  row.setAttribute("data-isrc", track.isrc);
  row.setAttribute("data-track", JSON.stringify(track));

  const rankValue = getRankValue(track, serviceName, displayRank);
  const isTotalService = serviceName === SERVICE_NAMES.TOTAL;

  if (isTotalService) {
    row.innerHTML = `
      <td class="rank">${rankValue}</td>
      ${renderCoverCellHtml(track)}
      ${renderTrackInfoCellHtml(track, serviceName)}
      <td class="spacer"></td>
      ${renderPlayCountCellsHtml(track, playCountMode)}
      <td class="seen-on" data-seen-on="${track.isrc}"></td>
      <td class="external" data-external="${track.isrc}"></td>
    `;

    const seenOnCell = row.querySelector(
      `[data-seen-on="${track.isrc}"]`
    ) as HTMLTableCellElement;
    if (seenOnCell) {
      displaySources(seenOnCell, track);
    }

    const externalCell = row.querySelector(
      `[data-external="${track.isrc}"]`
    ) as HTMLTableCellElement;
    if (externalCell && track.youtubeSource) {
      externalCell.appendChild(
        createSourceLinkFromService(track.youtubeSource, null, track)
      );
    }
  } else {
    row.innerHTML = `
      <td class="rank">${rankValue}</td>
      ${renderCoverCellHtml(track)}
      ${renderTrackInfoCellHtml(track, serviceName)}
      <td class="external" data-external="${track.isrc}"></td>
    `;

    const externalCell = row.querySelector(
      `[data-external="${track.isrc}"]`
    ) as HTMLTableCellElement;
    if (externalCell && track.youtubeSource) {
      externalCell.appendChild(
        createSourceLinkFromService(track.youtubeSource, null, track)
      );
    }
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
        track
      );
      sourcesContainer.appendChild(linkElement);
    }
  });

  cell.appendChild(sourcesContainer);
}

function createSourceLinkFromService(
  source: ServiceSource,
  rank: number | null = null,
  trackData: Track | null = null
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
        label.buttonType === "source_icon" && label.context === source.name
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
      `Play ${fullTrackName} by ${fullArtistName} on ${source.displayName}`
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

function createShowAllTracksRow(
  placeholderId: string,
  totalTrackCount: number,
  serviceName: string | null
): HTMLTableRowElement {
  const row = document.createElement("tr");
  row.className = "show-all-tracks-row";

  const cell = document.createElement("td");
  cell.colSpan = 4;
  cell.className = "show-all-tracks-cell";

  const button = document.createElement("button");
  button.className = "show-all-tracks-button";
  button.textContent = `Show All ${totalTrackCount} Tracks`;
  button.setAttribute("aria-label", `Show all ${totalTrackCount} tracks`);
  button.dataset.placeholderId = placeholderId;
  button.dataset.serviceName = serviceName || "";
  button.dataset.totalTrackCount = totalTrackCount.toString();

  cell.appendChild(button);
  row.appendChild(cell);

  return row;
}

const playlistDataCache = new Map<string, Playlist>();

export function setPlaylistData(data: Playlist[]): void {
  data.forEach((playlist) => {
    if (playlist.serviceName) {
      playlistDataCache.set(playlist.serviceName, playlist);
    }
  });
}

export function cachePlaylistData(
  serviceName: string,
  playlist: Playlist
): void {
  playlistDataCache.set(serviceName, playlist);
}

export function getPlaylistFromCache(
  serviceName: string
): Playlist | undefined {
  return playlistDataCache.get(serviceName);
}

export function getAllCachedPlaylists(): Playlist[] {
  return Array.from(playlistDataCache.values());
}

export function sortTable(column: string, order: string): void {
  const ranks = appRouter.getAvailableRanks();
  const rankConfig = ranks.find((rank) => rank.sortField === column);

  if (!rankConfig) {
    console.error(`Unknown sort column: ${column}`);
    return;
  }

  const tuneMeldPlaylist = getPlaylistFromCache(SERVICE_NAMES.TUNEMELD);
  if (!tuneMeldPlaylist) {
    return;
  }

  tuneMeldPlaylist.tracks?.sort((a, b) => {
    let aValue = (a as any)[rankConfig.dataField] as number;
    let bValue = (b as any)[rankConfig.dataField] as number;

    if (aValue == null) aValue = 0;
    if (bValue == null) bValue = 0;

    return order === "asc" ? aValue - bValue : bValue - aValue;
  });

  playlistDataCache.set(SERVICE_NAMES.TUNEMELD, tuneMeldPlaylist);

  renderPlaylistTracks(
    [tuneMeldPlaylist],
    "main-playlist-data-placeholder",
    SERVICE_NAMES.TUNEMELD,
    null,
    { forceRender: true }
  );
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

const buttonsWithListeners = new WeakSet<HTMLElement>();
let showAllListenerAdded = false;

export async function addToggleEventListeners() {
  const collapseButtons = document.querySelectorAll(".collapse-button");

  collapseButtons.forEach((button) => {
    const htmlButton = button as HTMLElement;

    if (buttonsWithListeners.has(htmlButton)) {
      return;
    }

    htmlButton.addEventListener("click", (event: Event) => {
      toggleCollapse(event);
    });

    buttonsWithListeners.add(htmlButton);
  });

  // Add event delegation for Show All buttons (only once)
  if (!showAllListenerAdded) {
    document.body.addEventListener("click", (event: Event) => {
      const target = event.target as HTMLElement;
      if (target && target.classList.contains("show-all-tracks-button")) {
        event.preventDefault();
        handleShowAllTracks(target);
      }
    });
    showAllListenerAdded = true;
  }

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
            isCollapsed
          );
        }
      }
    )
  );
}

function handleShowAllTracks(button: HTMLElement): void {
  const placeholderId = button.dataset.placeholderId;
  const serviceName = button.dataset.serviceName;

  if (!placeholderId || !serviceName) {
    return;
  }

  const playlist = getPlaylistFromCache(serviceName);
  if (!playlist) {
    return;
  }

  const placeholder = document.getElementById(placeholderId);
  if (placeholder) {
    placeholder.dataset.showAllTracks = "true";
  }

  const playlistId = `#${serviceName}-playlist`;
  const playlistContent = document.querySelector(
    `${playlistId} .playlist-content`
  ) as HTMLElement | null;
  const playlistElement = document.querySelector(
    playlistId
  ) as HTMLElement | null;

  if (playlistContent?.classList.contains("collapsed")) {
    playlistContent.classList.remove("collapsed");
  }
  if (playlistElement?.classList.contains("collapsed")) {
    playlistElement.classList.remove("collapsed");
  }

  const collapseButton = document.querySelector(
    `.collapse-button[data-target="${playlistId}"]`
  ) as HTMLElement | null;
  if (collapseButton) {
    collapseButton.textContent = "▼";
  }

  renderPlaylistTracks([playlist], placeholderId, serviceName, null, {
    showAllTracks: true,
  });
}

async function toggleCollapse(event: Event): Promise<void> {
  const button = (event.target || event.currentTarget) as HTMLElement;
  const targetId = button?.getAttribute("data-target");

  if (!targetId) {
    return;
  }

  const content = document.querySelector(
    `${targetId} .playlist-content`
  ) as HTMLElement | null;
  const playlist = document.querySelector(targetId) as HTMLElement | null;

  if (content) {
    content.classList.toggle("collapsed");
  }
  if (playlist) {
    playlist.classList.toggle("collapsed");
  }

  const isCollapsed = content?.classList.contains("collapsed") || false;

  // Extract service name from targetId (e.g., "#spotify-playlist" -> "spotify")
  const serviceName = targetId.replace("#", "").replace("-playlist", "");

  if (isCollapsed) {
    // REMOVE elements from DOM when collapsing
    const placeholderId = `${serviceName}-data-placeholder`;
    const dataContainerId = `${placeholderId}--data`;
    const dataContainer = document.getElementById(dataContainerId);
    if (dataContainer) {
      dataContainer.remove();
    }
  } else {
    // RE-RENDER playlist from cache when expanding
    const cachedPlaylist = getPlaylistFromCache(serviceName);
    if (cachedPlaylist) {
      const placeholderId = `${serviceName}-data-placeholder`;
      renderPlaylistTracks([cachedPlaylist], placeholderId, serviceName);
    }
  }

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
  isCollapsed: boolean
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
