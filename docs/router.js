import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "./selectors.js";
import { stateManager } from "./StateManager.js";
import { setupBodyClickListener } from "./servicePlayer.js";
import { errorHandler } from "./error-handler.js";
import { genreManager } from "./genre-manager.js";

class AppRouter {
  constructor() {
    this.router = new Navigo("/");
    this.currentGenre = null;
  }

  async initialize() {
    errorHandler.setRetryCallback(() => this.initialize());

    await genreManager.initialize();

    if (genreManager.hasValidData()) {
      this.setupRoutes();
      this.router.resolve();
    }
  }

  setupRoutes() {
    this.router.on("/:genre", async match => {
      await this.handleGenreRoute(match.data.genre);
    });

    this.router.on("/", async () => {
      await this.handleGenreRoute(genreManager.getDefaultGenre());
    });

    this.router.notFound(async () => {
      const defaultGenre = genreManager.getDefaultGenre();
      this.router.navigate(`/${defaultGenre}`);
      await this.handleGenreRoute(defaultGenre);
    });
  }

  async handleGenreRoute(genre) {
    if (!genreManager.hasValidData()) {
      return;
    }

    if (!genreManager.isValidGenre(genre)) {
      this.redirectToDefault();
      return;
    }

    await this.activateGenre(genre);
  }

  redirectToDefault() {
    const defaultGenre = genreManager.getDefaultGenre();
    if (defaultGenre) {
      this.navigateToGenre(defaultGenre);
    }
  }

  async activateGenre(genre) {
    this.currentGenre = genre;
    this.updatePageTitle(genre);
    this.syncGenreDropdown(genre);
    await this.loadGenreContent(genre);
  }

  updatePageTitle(genre) {
    const genreDisplay = genreManager.getDisplayName(genre);
    document.title = `tunemeld - ${genreDisplay}`;
  }

  syncGenreDropdown(genre) {
    const genreSelector = document.getElementById("genre-selector");
    if (genreSelector && genreSelector.value !== genre) {
      genreSelector.value = genre;
    }
  }

  async loadGenreContent(genre) {
    await updateGenreData(genre, stateManager.getViewCountType(), true);
    setupBodyClickListener(genre);
  }

  navigateToGenre(genre) {
    if (!this.router.routes || this.router.routes.length === 0) {
      this.setupRoutes();
    }

    this.router.navigate(`/${genre}`);
    this.router.resolve();
  }

  getCurrentGenre() {
    return this.currentGenre;
  }

  getAvailableGenres() {
    return genreManager.getAvailableGenres();
  }
}

export const appRouter = new AppRouter();
