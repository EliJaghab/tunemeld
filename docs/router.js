import Navigo from "https://cdn.jsdelivr.net/npm/navigo@8.11.1/+esm";
import { updateGenreData } from "./selectors.js";
import { stateManager } from "./StateManager.js";
import { graphqlClient } from "./graphql-client.js";
import { setupBodyClickListener } from "./servicePlayer.js";

class AppRouter {
  constructor() {
    this.router = new Navigo("/");
    this.currentGenre = null;
    this.availableGenres = [];
    this.defaultGenre = null;
  }

  async initialize() {
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
      this.showError("Unable to load genres from server. Please check your connection.");
      return;
    }

    this.setupRoutes();

    this.router.resolve();
  }

  setupRoutes() {
    // Genre route: /pop, /dance, etc.
    this.router.on("/:genre", async ({ data }) => {
      await this.handleGenreRoute(data.genre);
    });

    // Default/root route
    this.router.on("/", () => {
      this.navigateToGenre(this.defaultGenre);
    });

    this.router.notFound(() => {
      console.log("Route not found, redirecting to default genre");
      this.navigateToGenre(this.defaultGenre);
    });
  }

  async handleGenreRoute(genre) {
    // Validate genre exists in backend data
    const isValidGenre = this.availableGenres.some(g => g.name === genre);

    if (!isValidGenre) {
      console.log(`Invalid genre: ${genre}, redirecting to default`);
      this.navigateToGenre(this.defaultGenre);
      return;
    }

    // Update current state
    this.currentGenre = genre;

    // Update page title
    const genreDisplay = this.availableGenres.find(g => g.name === genre)?.displayName || genre;
    document.title = `tunemeld - ${genreDisplay}`;

    // Update genre selector
    const genreSelector = document.getElementById("genre-selector");
    if (genreSelector && genreSelector.value !== genre) {
      genreSelector.value = genre;
    }

    // Load genre data
    console.log(`Loading genre: ${genre}`);
    await updateGenreData(genre, stateManager.getViewCountType(), true);

    // Setup body click listener for this genre
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

  showError(message) {
    console.error("App Error:", message);

    // Show error in the main content area
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.innerHTML = `
        <div style="text-align: center; padding: 50px; color: #666;">
          <h2>⚠️ Unable to Load</h2>
          <p>${message}</p>
          <p>Please refresh the page or check your internet connection.</p>
        </div>
      `;
    }
  }
}

export const appRouter = new AppRouter();
