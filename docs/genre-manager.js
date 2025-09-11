import { graphqlClient } from "./graphql-client.js";
import { errorHandler } from "./error-handler.js";

class GenreManager {
  constructor() {
    this.availableGenres = [];
    this.defaultGenre = null;
    this.isLoaded = false;
  }

  async initialize() {
    if (this.isLoaded) return;

    try {
      const data = await graphqlClient.getAvailableGenres();
      this.availableGenres = data.genres;
      this.defaultGenre = data.defaultGenre;

      if (!this.availableGenres || this.availableGenres.length === 0) {
        throw new Error("No genres returned from backend");
      }

      this.isLoaded = true;
    } catch (error) {
      this.handleLoadError(error);
      throw error;
    }
  }

  handleLoadError(error) {
    this.availableGenres = [];
    this.defaultGenre = null;
    this.isLoaded = false;

    const technicalDetails = error.stack
      ? `${error.message}\n\nStack trace:\n${error.stack}`
      : error.message;

    errorHandler.showError(
      "Genre loading service is currently unavailable. Some features may be limited.",
      technicalDetails,
    );
  }

  getAvailableGenres() {
    return this.availableGenres;
  }

  getDefaultGenre() {
    return this.defaultGenre;
  }

  isValidGenre(genre) {
    return this.availableGenres.some((g) => g.name === genre);
  }

  getDisplayName(genre) {
    const found = this.availableGenres.find((g) => g.name === genre);
    return found?.displayName || genre;
  }

  hasValidData() {
    return (
      this.isLoaded && this.availableGenres.length > 0 && this.defaultGenre
    );
  }
}

export const genreManager = new GenreManager();
