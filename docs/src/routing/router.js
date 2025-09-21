import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "@/utils/selectors.js";
import { stateManager } from "@/state/StateManager.js";
import { setupBodyClickListener } from "@/components/servicePlayer.js";
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

      if (genre && this.isValidGenre(genre)) {
        // Use default rank if none specified, but don't redirect
        const rankToUse = rank || this.getDefaultRank();
        await this.handleGenreRoute(genre, rankToUse);
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

  async handleGenreRoute(genre, rank) {
    if (!this.hasValidData()) {
      return;
    }

    if (!this.isValidGenre(genre)) {
      this.redirectToDefault();
      return;
    }

    await this.activateGenre(genre, rank);
  }

  redirectToDefault() {
    const defaultGenre = this.getDefaultGenre();
    if (defaultGenre) {
      const defaultRank = this.getDefaultRank();
      this.navigateToGenre(defaultGenre, defaultRank);
    }
  }

  async activateGenre(genre, rank) {
    const genreChanged = this.currentGenre !== genre;
    const needsFullUpdate = genreChanged || this.isInitialLoad;

    this.currentGenre = genre;
    this.updatePageTitle(genre);
    this.syncGenreButtons(genre);
    this.syncRankState(rank);
    await this.loadGenreContent(genre, needsFullUpdate);

    this.isInitialLoad = false;
  }

  updatePageTitle(genre) {
    const genreDisplay = this.getGenreDisplayName(genre);
    document.title = `tunemeld - ${genreDisplay}`;
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
