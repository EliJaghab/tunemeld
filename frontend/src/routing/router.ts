// @ts-ignore: Navigo is imported from CDN and has its own types
import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "@/utils/selectors";
import { debugLog } from "@/config/config";
import { stateManager } from "@/state/StateManager";
import {
  setupBodyClickListener,
  openTrackFromUrl,
} from "@/components/servicePlayer";
import { errorHandler } from "@/utils/error-handler";
import { showInitialShimmer } from "@/components/shimmer";
import { graphqlClient } from "@/services/graphql-client";
import type { Genre, Rank, Track } from "@/types";

const ROUTER_LOG_PREFIX = "[Router]";
const routerDebug = (message: string, meta?: unknown) => {
  debugLog("Router", message, meta);
};

// Define track info interface for page title updates
interface TrackInfo {
  trackName: string;
  artistName: string;
}

// Navigo router interface for type safety
interface NavigoRouter {
  on(route: string, handler: () => void | Promise<void>): NavigoRouter;
  notFound(handler: () => void | Promise<void>): NavigoRouter;
  resolve(): NavigoRouter;
  routes?: any[];
}

class AppRouter {
  private router: NavigoRouter;
  private genres: { genres: Genre[]; defaultGenre: string } | null;
  private ranks: Rank[] | null;
  private isInitialLoad: boolean;

  constructor() {
    this.router = new Navigo("/");
    this.genres = null;
    this.ranks = null;
    this.isInitialLoad = true;
  }

  async initialize(): Promise<void> {
    routerDebug("initialize: start");
    errorHandler.setRetryCallback(() => this.initialize());

    // Show content with shimmer immediately to prevent blank screen
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.style.visibility = "visible";
    }
    document.body.style.transition = "opacity 0.2s ease-in";
    document.body.style.opacity = "1";
    showInitialShimmer();

    try {
      const staticConfig = await graphqlClient.getStaticConfig();
      routerDebug("initialize: static config fetched");

      // Store in router for routing logic
      this.genres = {
        genres: staticConfig.genres,
        defaultGenre: staticConfig.genres?.[0]?.name || "pop",
      };
      this.ranks = staticConfig.ranks;

      // Populate StateManager with static config
      stateManager.setRanks(staticConfig.ranks);
      stateManager.setGenres(staticConfig.genres);
      stateManager.setButtonLabels({
        closePlayer: staticConfig.closePlayerLabels,
        themeToggleLight: staticConfig.themeToggleLightLabels,
        themeToggleDark: staticConfig.themeToggleDarkLabels,
        acceptTerms: staticConfig.acceptTermsLabels,
        moreButtonAppleMusic: staticConfig.moreButtonAppleMusicLabels,
        moreButtonSoundcloud: staticConfig.moreButtonSoundcloudLabels,
        moreButtonSpotify: staticConfig.moreButtonSpotifyLabels,
        moreButtonYoutube: staticConfig.moreButtonYoutubeLabels,
      });

      // Set the default rank field
      const defaultRank = this.ranks?.find((rank) => rank.isDefault);
      if (defaultRank) {
        stateManager.setDefaultRankField(defaultRank.sortField);
      }

      // Initialize current genre from URL to prevent flash
      const urlParams = new URLSearchParams(window.location.search);
      const genreFromUrl = urlParams.get("genre");
      if (genreFromUrl && this.isValidGenre(genreFromUrl)) {
        stateManager.setCurrentGenre(genreFromUrl);
      }

      this.setupRoutes();
      this.router.resolve();
      routerDebug("initialize: end");
    } catch (error) {
      console.error("Router initialization failed:", error);
      throw error;
    }
  }

  setupRoutes(): void {
    this.router.on("/", async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const genre = urlParams.get("genre");
      const rank = urlParams.get("rank");
      const player = urlParams.get("player");
      const isrc = urlParams.get("isrc");

      if (genre && this.isValidGenre(genre)) {
        // Use default rank if none specified, but don't redirect
        const rankToUse = rank || this.getDefaultRank();
        await this.handleGenreRoute(genre, rankToUse || null, player, isrc);
      } else {
        const defaultGenre = this.getDefaultGenre();
        const defaultRank = this.getDefaultRank();
        if (defaultGenre) {
          const url = this.buildUrl(defaultGenre, defaultRank || null);
          window.history.replaceState({}, "", url);
          await this.handleGenreRoute(defaultGenre, defaultRank || null);
        }
      }
    });

    this.router.notFound(async () => {
      this.redirectToDefault();
    });
  }

  async handleGenreRoute(
    genre: string,
    rank: string | null,
    player: string | null = null,
    isrc: string | null = null,
  ): Promise<void> {
    if (!this.hasValidData()) {
      return;
    }

    if (!this.isValidGenre(genre)) {
      this.redirectToDefault();
      return;
    }

    await this.activateGenre(genre, rank, player, isrc);
  }

  redirectToDefault(): void {
    const defaultGenre = this.getDefaultGenre();
    if (defaultGenre) {
      const defaultRank = this.getDefaultRank();
      this.navigateToGenre(defaultGenre, defaultRank);
    }
  }

  async activateGenre(
    genre: string,
    rank: string | null,
    player: string | null = null,
    isrc: string | null = null,
  ): Promise<void> {
    const genreChanged = stateManager.getCurrentGenre() !== genre;
    const needsFullUpdate = genreChanged || this.isInitialLoad;

    // Check if rank changed before we update state
    const previousRank = stateManager.getCurrentColumn();
    const currentRankField = rank || this.getDefaultRank();
    const rankChanged = previousRank !== currentRankField;

    // Only load content if genre changed or initial load
    // Never reload content when just opening/closing player within same genre
    const shouldLoadContent = needsFullUpdate;

    // Show shimmer for genre switches (but not initial load - that's handled separately)
    if (genreChanged && !this.isInitialLoad) {
      const { showGenreSwitchShimmer } = await import("@/components/shimmer");
      showGenreSwitchShimmer();
    }

    stateManager.setCurrentGenre(genre);
    this.updatePageTitle(genre);
    this.updateFavicon(genre);
    this.syncGenreButtons(genre);
    this.syncRankState(rank);
    this.syncTrackState(player, isrc);

    if (shouldLoadContent) {
      await this.loadGenreContent(genre, needsFullUpdate);
    } else if (rankChanged && !genreChanged && !this.isInitialLoad) {
      const { showRankSwitchShimmer, hideShimmerLoaders } = await import(
        "@/components/shimmer"
      );
      const { sortTable } = await import("@/components/playlist");

      const shimmerStartTime = performance.now();
      showRankSwitchShimmer();

      const newRankField = stateManager.getCurrentColumn();
      const newOrder = stateManager.getCurrentOrder();
      if (newRankField) {
        // Wait for shimmer to paint before sorting
        await new Promise((resolve) =>
          requestAnimationFrame(() => resolve(null)),
        );
        sortTable(newRankField, newOrder);

        // Ensure shimmer is visible for at least 150ms before hiding
        const shimmerDuration = performance.now() - shimmerStartTime;
        const minShimmerDuration = 150;
        const remainingTime = Math.max(0, minShimmerDuration - shimmerDuration);

        if (remainingTime > 0) {
          await new Promise((resolve) => setTimeout(resolve, remainingTime));
        }

        // Wait for sort to paint before hiding shimmer
        await new Promise((resolve) =>
          requestAnimationFrame(() => resolve(null)),
        );
        hideShimmerLoaders();
      }
    }

    if (player && isrc) {
      await this.openTrackPlayer(genre, player, isrc);
    }

    this.isInitialLoad = false;
  }

  updatePageTitle(genre: string, trackInfo: TrackInfo | null = null): void {
    if (trackInfo && trackInfo.trackName && trackInfo.artistName) {
      document.title = `${trackInfo.trackName} - ${trackInfo.artistName}`;
    } else {
      const genreDisplay = this.getGenreDisplayName(genre);
      document.title = `tunemeld - ${genreDisplay}`;
    }
  }

  updateTitleWithTrackInfo(trackName: string, artistName: string): void {
    document.title = `${trackName} - ${artistName}`;
  }

  updateFavicon(genre: string): void {
    const genreData = this.getAvailableGenres().find((g) => g.name === genre);
    if (genreData && genreData.iconUrl) {
      // Remove existing favicon
      const existingFavicon =
        document.querySelector('link[rel="icon"]') ||
        document.querySelector('link[rel="shortcut icon"]');
      if (existingFavicon) {
        existingFavicon.remove();
      }

      // Add new favicon
      const newFavicon = document.createElement("link");
      newFavicon.rel = "icon";
      newFavicon.type = "image/png";
      newFavicon.href = genreData.iconUrl;
      document.head.appendChild(newFavicon);
    }
  }

  syncGenreButtons(genre: string): void {
    document.querySelectorAll(".genre-controls .sort-button").forEach((btn) => {
      btn.classList.remove("active");
      if (btn.getAttribute("data-genre") === genre) {
        btn.classList.add("active");
      }
    });
  }

  syncRankState(rank: string | null): void {
    // Use backend default if no rank specified
    const sortField = rank || this.getDefaultRank();
    if (sortField) {
      stateManager.setCurrentColumn(sortField);
    }

    // Find the rank configuration to get the sort order
    const rankConfig = this.ranks?.find((r) => r.sortField === sortField);
    if (rankConfig) {
      stateManager.setCurrentOrder(rankConfig.sortOrder);
    }
  }

  syncTrackState(player: string | null, isrc: string | null): void {
    if (player && isrc) {
      stateManager.setCurrentTrack(isrc, player);
    } else {
      stateManager.clearCurrentTrack();
    }
  }

  async loadGenreContent(
    genre: string,
    fullUpdate: boolean = true,
  ): Promise<void> {
    routerDebug("loadGenreContent: start", { genre, fullUpdate });
    // Show initial shimmer only on first app load
    const wasInitialLoad = this.isInitialLoad;
    routerDebug("loadGenreContent:start", {
      genre,
      fullUpdate,
      wasInitialLoad,
    });
    if (this.isInitialLoad) {
      routerDebug("loadGenreContent: initial load");
      this.isInitialLoad = false;
    }

    await updateGenreData(genre, fullUpdate, wasInitialLoad);
    if (fullUpdate) {
      setupBodyClickListener(genre);
    }
    routerDebug("loadGenreContent: end", { genre, fullUpdate });
    routerDebug("loadGenreContent:end", {
      genre,
      fullUpdate,
    });
  }

  private buildUrl(
    genre: string,
    rank: string | null = null,
    player: string | null = null,
    isrc: string | null = null,
  ): string {
    let url = `/?genre=${encodeURIComponent(genre)}`;
    if (rank) {
      url += `&rank=${encodeURIComponent(rank)}`;
    }
    if (player) {
      url += `&player=${encodeURIComponent(player)}`;
    }
    if (isrc) {
      url += `&isrc=${encodeURIComponent(isrc)}`;
    }
    return url;
  }

  navigateToGenre(genre: string, rank: string | null = null): void {
    if (!this.router.routes || this.router.routes.length === 0) {
      this.setupRoutes();
    }

    const url = this.buildUrl(genre, rank);
    window.history.pushState({}, "", url);
    this.router.resolve();
  }

  navigateToRank(sortField: string): void {
    const currentGenre = this.getCurrentGenre();
    if (currentGenre) {
      this.navigateToGenre(currentGenre, sortField);
    }
  }

  navigateToTrack(
    genre: string,
    rank: string | null,
    player: string | null,
    isrc: string | null,
  ): void {
    if (!this.router.routes || this.router.routes.length === 0) {
      this.setupRoutes();
    }

    const url = this.buildUrl(genre, rank, player, isrc);
    window.history.pushState({}, "", url);
    this.router.resolve();
  }

  updateUrlOnly(
    genre: string,
    rank: string | null,
    player: string | null,
    isrc: string | null,
  ): void {
    const url = this.buildUrl(genre, rank, player, isrc);
    window.history.replaceState({}, "", url);
  }

  async openTrackPlayer(
    genre: string,
    player: string,
    isrc: string,
  ): Promise<boolean | void> {
    // Wait a bit for the playlist to be loaded
    await new Promise((resolve) => setTimeout(resolve, 100));
    return await openTrackFromUrl(genre, player, isrc);
  }

  getCurrentGenre(): string | null {
    return stateManager.getCurrentGenre();
  }

  // Genre helpers
  getAvailableGenres(): Genre[] {
    return this.genres?.genres || [];
  }

  getDefaultGenre(): string | undefined {
    return this.genres?.defaultGenre;
  }

  isValidGenre(genre: string): boolean {
    return this.getAvailableGenres().some((g) => g.name === genre);
  }

  getGenreDisplayName(genre: string): string {
    const found = this.getAvailableGenres().find((g) => g.name === genre);
    return found?.displayName || genre;
  }

  // Rank helpers
  getAvailableRanks(): Rank[] {
    return this.ranks || [];
  }

  getDefaultRank(): string | undefined {
    const defaultRank = this.ranks?.find((rank) => rank.isDefault);
    return (
      defaultRank?.sortField || stateManager.getDefaultRankField() || undefined
    );
  }

  isValidRank(rank: string): boolean {
    return this.ranks?.some((r) => r.sortField === rank) || false;
  }

  getRankDisplayName(rank: string): string {
    const found = this.ranks?.find((r) => r.sortField === rank);
    return found?.displayName || rank;
  }

  hasValidData(): boolean {
    return !!(
      this.genres &&
      this.ranks &&
      this.getAvailableGenres().length > 0 &&
      this.getDefaultGenre()
    );
  }
}

export const appRouter = new AppRouter();
