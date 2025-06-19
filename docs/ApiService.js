/**
 * ApiService - Centralized API Management for TuneMeld Frontend
 *
 * ARCHITECTURAL PURPOSE:
 * This service addresses API management issues by centralizing all API calls
 * that were previously scattered across playlist.js, header.js, and chart.js.
 *
 * PROBLEMS SOLVED:
 * 1. Code Duplication: Eliminates repeated fetch logic and error handling
 * 2. Inconsistent Error Handling: Provides standardized error handling patterns
 * 3. API Endpoint Management: Centralized URL construction and response handling
 * 4. Testing: Enables easy mocking and testing of API interactions
 *
 * DESIGN PRINCIPLES:
 * - Consistent Error Handling: All methods use standardized error handling
 * - Response Normalization: Handles Django's wrapped response format consistently
 * - Minimal Breaking Changes: Maintains existing function signatures during migration
 * - Clear Separation: Pure API logic separated from DOM manipulation
 *
 * MIGRATION STRATEGY:
 * Phase 1: Extract existing API calls with minimal changes (current implementation)
 * Phase 2: Add request caching and retry logic
 * Phase 3: Add request batching and optimization
 */

import { DJANGO_API_BASE_URL } from "./config.js";

class ApiService {
  constructor() {
    this.baseUrl = DJANGO_API_BASE_URL;
  }

  /**
   * Generic fetch wrapper with consistent error handling
   * @param {string} url - The URL to fetch
   * @param {Object} options - Fetch options
   * @returns {Promise<any>} - Parsed response data
   */
  async fetchWithErrorHandling(url, options = {}) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch ${url}`);
      }
      const responseData = await response.json();
      // Handle Django's wrapped response format
      return responseData.data || responseData;
    } catch (error) {
      console.error(`API Error for ${url}:`, error);
      throw error;
    }
  }

  /**
   * Fetch last updated date for a genre
   * @param {string} genre - The genre to fetch
   * @returns {Promise<Object>} - Last updated data
   */
  async fetchLastUpdated(genre) {
    const url = `${this.baseUrl}/last-updated/${genre}`;
    return this.fetchWithErrorHandling(url);
  }

  /**
   * Fetch playlist data for a genre
   * @param {string} genre - The genre to fetch
   * @returns {Promise<Array>} - Playlist data
   */
  async fetchPlaylistData(genre) {
    const url = `${this.baseUrl}/playlist-data/${genre}`;
    return this.fetchWithErrorHandling(url);
  }

  /**
   * Fetch service-specific playlist data
   * @param {string} genre - The genre to fetch
   * @param {string} service - The service name (AppleMusic, SoundCloud, Spotify)
   * @returns {Promise<Array>} - Service playlist data
   */
  async fetchServicePlaylist(genre, service) {
    const url = `${this.baseUrl}/service-playlist/${genre}/${service}`;
    return this.fetchWithErrorHandling(url);
  }

  /**
   * Fetch header art data for a genre
   * @param {string} genre - The genre to fetch
   * @returns {Promise<Object>} - Header art data
   */
  async fetchHeaderArt(genre) {
    const url = `${this.baseUrl}/header-art/${genre}`;
    return this.fetchWithErrorHandling(url);
  }

  /**
   * Fetch chart data for a genre
   * @param {string} genre - The genre to fetch
   * @returns {Promise<Array>} - Chart data
   */
  async fetchChartData(genre) {
    const url = `${this.baseUrl}/graph-data/${genre}`;
    return this.fetchWithErrorHandling(url);
  }

  /**
   * Fetch chart HTML content
   * @returns {Promise<string>} - HTML content
   */
  async fetchChartHtml() {
    try {
      const response = await fetch("html/chart.html");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch chart HTML`);
      }
      return response.text();
    } catch (error) {
      console.error("API Error for chart HTML:", error);
      throw error;
    }
  }

  /**
   * Load external JavaScript library
   * @param {string} src - The script source URL
   * @returns {Promise<void>}
   */
  async loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
}

export const apiService = new ApiService();
