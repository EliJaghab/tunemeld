import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "./selectors.js";
import { stateManager } from "./StateManager.js";
import { graphqlClient } from "./graphql-client.js";
import { setupBodyClickListener } from "./servicePlayer.js";
import { errorHandler } from "./error-handler.js";

class AppRouter {
  constructor() {
    this.router = new Navigo("/");
    this.currentGenre = null;
    this.availableGenres = [];
    this.defaultGenre = null;
  }

  async initialize() {
    let graphqlError = null;

    errorHandler.setRetryCallback(() => this.initialize());

    try {
      const data = await graphqlClient.getAvailableGenres();
      this.availableGenres = data.genres;
      this.defaultGenre = data.defaultGenre;
      if (!this.availableGenres || this.availableGenres.length === 0) {
        throw new Error("No genres returned from backend");
      }
      console.log(
        "Available genres:",
        this.availableGenres.map(g => g.name)
      );
      console.log("Default genre from backend:", this.defaultGenre);
    } catch (error) {
      console.error("Failed to load genres from backend:", error);
      graphqlError = error;

      this.availableGenres = [];
      this.defaultGenre = null;

      let technicalDetails = error.message;
      if (error.stack) {
        technicalDetails += "\n\nStack trace:\n" + error.stack;
      }

      errorHandler.showError(
        "Genre loading service is currently unavailable. Some features may be limited.",
        technicalDetails
      );
    }

    if (this.availableGenres.length > 0 && this.defaultGenre) {
      this.setupRoutes();
      this.router.resolve();
    } else {
      console.log("Skipping route setup - no genre data available. Static content only.");
    }

    if (graphqlError) {
      console.log("Continuing with limited functionality due to GraphQL error");
    }
  }

  setupRoutes() {
    this.router.on("/:genre", async ({ data }) => {
      await this.handleGenreRoute(data.genre);
    });

    this.router.on("/", () => {
      this.navigateToGenre(this.defaultGenre);
    });

    this.router.notFound(() => {
      console.log("Route not found, redirecting to default genre");
      this.navigateToGenre(this.defaultGenre);
    });
  }

  async handleGenreRoute(genre) {
    const isValidGenre = this.availableGenres.some(g => g.name === genre);

    if (!isValidGenre) {
      console.log(`Invalid genre: ${genre}, redirecting to default`);
      this.navigateToGenre(this.defaultGenre);
      return;
    }

    this.currentGenre = genre;

    const genreDisplay = this.availableGenres.find(g => g.name === genre)?.displayName || genre;
    document.title = `tunemeld - ${genreDisplay}`;
    const genreSelector = document.getElementById("genre-selector");
    if (genreSelector && genreSelector.value !== genre) {
      genreSelector.value = genre;
    }

    console.log(`Loading genre: ${genre}`);
    await updateGenreData(genre, stateManager.getViewCountType(), true);
    setupBodyClickListener(genre);
  }

  // Public API
  navigateToGenre(genre) {
    this.router.navigate(`/${genre}`);
  }

  getCurrentGenre() {
    return this.currentGenre;
  }

  getAvailableGenres() {
    return this.availableGenres;
  }
}

export const appRouter = new AppRouter();
