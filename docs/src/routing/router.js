import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "@/utils/selectors.js";
import { stateManager } from "@/state/StateManager.js";
import {
  setupBodyClickListener,
  openTrackFromUrl,
} from "@/components/servicePlayer.js";
import { errorHandler } from "@/utils/error-handler.js";
import { showInitialShimmer } from "@/components/shimmer.js";
import { graphqlClient } from "@/services/graphql-client.js";

class AppRouter {
  constructor() {
    this.router = new Navigo("/");
    this.currentGenre = null;
    this.genres = null;
    this.ranks = null;
    this.isInitialLoad = true;
  }

  async initialize() {
    errorHandler.setRetryCallback(() => this.initialize());

    try {
      const [genreData, rankData] = await Promise.all([
        graphqlClient.getAvailableGenres(),
        graphqlClient.fetchPlaylistRanks(),
      ]);

      this.genres = genreData;
      this.ranks = rankData.ranks;

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

  setupRoutes() {
    this.router.on("/", async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const genre = urlParams.get("genre");
      const rank = urlParams.get("rank");
      const player = urlParams.get("player");
      const isrc = urlParams.get("isrc");

      if (genre && this.isValidGenre(genre)) {
        // Use default rank if none specified, but don't redirect
        const rankToUse = rank || this.getDefaultRank();
        await this.handleGenreRoute(genre, rankToUse, player, isrc);
      } else {
        const defaultGenre = this.getDefaultGenre();
        const defaultRank = this.getDefaultRank();
        // Update URL without triggering another resolve to prevent double-loading
        let url = `/?genre=${encodeURIComponent(defaultGenre)}`;
        if (defaultRank) {
          url += `&rank=${encodeURIComponent(defaultRank)}`;
        }
        window.history.replaceState({}, "", url);
        await this.handleGenreRoute(defaultGenre, defaultRank);
      }
    });

    this.router.notFound(async () => {
      this.redirectToDefault();
    });
  }

  async handleGenreRoute(genre, rank, player = null, isrc = null) {
    if (!this.hasValidData()) {
      return;
    }

    if (!this.isValidGenre(genre)) {
      this.redirectToDefault();
      return;
    }

    await this.activateGenre(genre, rank, player, isrc);
  }

  redirectToDefault() {
    const defaultGenre = this.getDefaultGenre();
    if (defaultGenre) {
      const defaultRank = this.getDefaultRank();
      this.navigateToGenre(defaultGenre, defaultRank);
    }
  }

  async activateGenre(genre, rank, player = null, isrc = null) {
    const genreChanged = this.currentGenre !== genre;
    const needsFullUpdate = genreChanged || this.isInitialLoad;

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

  updatePageTitle(genre) {
    const genreDisplay = this.getGenreDisplayName(genre);
    document.title = `tunemeld - ${genreDisplay}`;
  }

  updateFavicon(genre) {
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

  syncGenreButtons(genre) {
    document.querySelectorAll(".genre-controls .sort-button").forEach((btn) => {
      btn.classList.remove("active");
      if (btn.getAttribute("data-genre") === genre) {
        btn.classList.add("active");
      }
    });
  }

  syncRankState(rank) {
    // Use backend default if no rank specified
    const sortField = rank || this.getDefaultRank();
    stateManager.setCurrentColumn(sortField);

    // Find the rank configuration to get the sort order
    const rankConfig = this.ranks?.find((r) => r.sortField === sortField);
    if (rankConfig) {
      stateManager.setCurrentOrder(rankConfig.sortOrder);
    }
  }

  syncTrackState(player, isrc) {
    if (player && isrc) {
      stateManager.setCurrentTrack(isrc, player);
    } else {
      stateManager.clearCurrentTrack();
    }
  }

  async loadGenreContent(genre, fullUpdate = true) {
    // Show initial shimmer only on first app load
    if (this.isInitialLoad) {
      showInitialShimmer();
      this.isInitialLoad = false;
    }

    await updateGenreData(genre, fullUpdate);
    if (fullUpdate) {
      setupBodyClickListener(genre);
    }
  }

  navigateToGenre(genre, rank = null) {
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

  navigateToRank(sortField) {
    const currentGenre = this.getCurrentGenre();
    if (currentGenre) {
      this.navigateToGenre(currentGenre, sortField);
    }
  }

  navigateToTrack(genre, rank, player, isrc) {
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

  async openTrackPlayer(genre, player, isrc) {
    // Wait a bit for the playlist to be loaded
    await new Promise((resolve) => setTimeout(resolve, 100));
    return await openTrackFromUrl(genre, player, isrc);
  }

  getCurrentGenre() {
    return this.currentGenre;
  }

  // Genre helpers
  getAvailableGenres() {
    return this.genres?.genres || [];
  }

  getDefaultGenre() {
    return this.genres?.defaultGenre;
  }

  isValidGenre(genre) {
    return this.getAvailableGenres().some((g) => g.name === genre);
  }

  getGenreDisplayName(genre) {
    const found = this.getAvailableGenres().find((g) => g.name === genre);
    return found?.displayName || genre;
  }

  // Rank helpers
  getAvailableRanks() {
    return this.ranks || [];
  }

  getDefaultRank() {
    const defaultRank = this.ranks?.find((rank) => rank.isDefault);
    return defaultRank?.sortField || stateManager.getDefaultRankField();
  }

  isValidRank(rank) {
    return this.ranks?.some((r) => r.sortField === rank) || false;
  }

  getRankDisplayName(rank) {
    const found = this.ranks?.find((r) => r.sortField === rank);
    return found?.displayName || rank;
  }

  hasValidData() {
    return (
      this.genres &&
      this.ranks &&
      this.getAvailableGenres().length > 0 &&
      this.getDefaultGenre()
    );
  }
}

export const appRouter = new AppRouter();
