// @ts-ignore: Navigo is imported from CDN and has its own types
import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "@/utils/selectors";
import { stateManager } from "@/state/StateManager";
import {
  setupBodyClickListener,
  openTrackFromUrl,
} from "@/components/servicePlayer";
import { errorHandler } from "@/utils/error-handler";
import { showInitialShimmer } from "@/components/shimmer";
import { graphqlClient } from "@/services/graphql-client";
import type { Genre, Rank, Track } from "@/types";

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
  private currentGenre: string | null;
  private genres: { genres: Genre[]; defaultGenre: string } | null;
  private ranks: Rank[] | null;
  private isInitialLoad: boolean;

  constructor() {
    this.router = new Navigo("/");
    this.currentGenre = null;
    this.genres = null;
    this.ranks = null;
    this.isInitialLoad = true;
  }

  async initialize(): Promise<void> {
    errorHandler.setRetryCallback(() => this.initialize());

    try {
      // Wait for the massive query data to be available
      const { getGlobalPageData } = await import("@/utils/selectors");
      let globalData = getGlobalPageData();

      console.log("[DEBUG ROUTER] globalData exists?", !!globalData);

      // If no global data yet, trigger the initial load
      if (!globalData) {
        console.log(
          "[DEBUG ROUTER] No global data - calling updateGenreData(pop, true)",
        );
        this.isInitialLoad = false; // Mark as no longer initial to prevent duplicate loading
        const { updateGenreData } = await import("@/utils/selectors");
        await updateGenreData("pop", true);
        globalData = getGlobalPageData();
        this.currentGenre = "pop"; // Track that we loaded pop data
      } else {
        console.log(
          "[DEBUG ROUTER] Global data already exists - skipping initial load",
        );
      }

      if (globalData) {
        // Get genres from the focused query instead of making separate call
        this.genres = globalData.genres;
        this.ranks = globalData.ranks.ranks;
      }

      // Set the default rank field in StateManager
      const defaultRank = this.ranks?.find((rank) => rank.isDefault);
      if (defaultRank) {
        stateManager.setDefaultRankField(defaultRank.sortField);
      }

      this.setupRoutes();
      this.router.resolve();
    } catch (error) {
      console.error("Router initialization failed:", error);
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
          // Update URL without triggering another resolve to prevent double-loading
          let url = `/?genre=${encodeURIComponent(defaultGenre)}`;
          if (defaultRank) {
            url += `&rank=${encodeURIComponent(defaultRank)}`;
          }
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
    const genreChanged = this.currentGenre !== genre;
    const needsFullUpdate = genreChanged || this.isInitialLoad;

    console.log(
      `[DEBUG ROUTER] activateGenre: currentGenre=${this.currentGenre}, requestedGenre=${genre}, genreChanged=${genreChanged}, isInitialLoad=${this.isInitialLoad}, needsFullUpdate=${needsFullUpdate}`,
    );

    this.currentGenre = genre;
    this.updatePageTitle(genre);
    this.updateFavicon(genre);
    this.syncGenreButtons(genre);
    this.syncRankState(rank);
    this.syncTrackState(player, isrc);
    await this.loadGenreContent(genre, needsFullUpdate);

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
    // Show initial shimmer only on first app load
    const wasInitialLoad = this.isInitialLoad;
    if (this.isInitialLoad) {
      showInitialShimmer();
      this.isInitialLoad = false;
    }

    await updateGenreData(genre, fullUpdate, wasInitialLoad);
    if (fullUpdate) {
      setupBodyClickListener(genre);
    }
  }

  navigateToGenre(genre: string, rank: string | null = null): void {
    if (!this.router.routes || this.router.routes.length === 0) {
      this.setupRoutes();
    }

    let url = `/?genre=${encodeURIComponent(genre)}`;
    if (rank) {
      url += `&rank=${encodeURIComponent(rank)}`;
    }
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
    window.history.pushState({}, "", url);
    this.router.resolve();
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
    return this.currentGenre;
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
