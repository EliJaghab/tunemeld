/**
 * StateManager - Centralized State Management for TuneMeld Frontend
 *
 * ARCHITECTURAL PURPOSE:
 * This class addresses critical frontend architecture issues by centralizing application state
 * that was previously scattered across DOM attributes, module-level variables, and localStorage.
 *
 * PROBLEMS SOLVED:
 * 1. DOM-based State Dependencies: Eliminates brittle queries like
 *    `document.querySelector(".sort-button[data-order]").getAttribute("data-column")`
 * 2. Circular Dependencies: Breaks the circular import cycle between selectors.js ↔ playlist.js
 * 3. State Consistency: Provides single source of truth for UI state across components
 * 4. Testability: Enables unit testing by removing direct DOM dependencies
 *
 * DESIGN PRINCIPLES:
 * - Minimal API surface: Simple getters/setters matching existing function signatures
 * - Backward Compatibility: Maintains existing behavior during migration
 * - Progressive Enhancement: Can be extended with reactive updates in future phases
 *
 * MIGRATION STRATEGY:
 * Phase 1: Replace DOM queries with centralized state (current implementation)
 * Phase 2: Add reactive state updates and event emission
 * Phase 3: Extend to manage genre, theme, and playlist data
 */
import { SHIMMER_TYPES, TUNEMELD_RANK_FIELD } from "../config/constants.js";
class StateManager {
  constructor() {
    this.state = {
      sortColumn: null, // Will be set from backend default
      sortOrder: "asc",
      theme: null,
      currentGenre: null,
      currentIsrc: null,
      currentPlayer: null,
      defaultRankField: null, // Store the default from backend
      shimmer: {
        services: false,
        playlist: false,
        isInitialLoad: false,
        currentType: SHIMMER_TYPES.TUNEMELD,
      },
      modals: {
        activeDescriptionModals: new Set(),
      },
    };
    this.domElements = new Map();
  }
  initializeFromDOM() {
    // Sort column will be set from backend default
    this.state.sortOrder = "asc";
    // Initialize theme - it may already be applied by inline script
    const storedTheme = localStorage.getItem("theme");
    this.state.theme = storedTheme || this.getTimeBasedTheme();
  }
  getTimeBasedTheme() {
    const hour = new Date().getHours();
    return hour >= 19 || hour < 7 ? "dark" : "light";
  }
  getCurrentColumn() {
    return this.state.sortColumn;
  }
  setCurrentColumn(column) {
    this.state.sortColumn = column;
  }
  getCurrentOrder() {
    return this.state.sortOrder;
  }
  isRankActive(rankSortField) {
    return rankSortField === this.getCurrentColumn();
  }
  setCurrentOrder(order) {
    this.state.sortOrder = order;
  }
  setDefaultRankField(field) {
    this.state.defaultRankField = field;
    // If no sort column set yet, use the default
    if (!this.state.sortColumn) {
      this.state.sortColumn = field;
    }
  }
  getDefaultRankField() {
    return this.state.defaultRankField;
  }
  isSortingByDefaultRank() {
    return this.state.sortColumn === this.state.defaultRankField;
  }
  // Theme Management
  getTheme() {
    return this.state.theme;
  }
  setTheme(theme) {
    this.state.theme = theme;
    localStorage.setItem("theme", theme);
    this.applyTheme(theme);
  }
  toggleTheme() {
    const newTheme = this.state.theme === "dark" ? "light" : "dark";
    this.setTheme(newTheme);
    return newTheme;
  }
  applyTheme(theme) {
    const isDarkMode = theme === "dark";
    // Remove loading state and apply proper theme
    document.documentElement.classList.remove("dark-mode-loading");
    document.body.classList.toggle("dark-mode", isDarkMode);
    const themeToggleButton = this.getElement("theme-toggle-button");
    if (themeToggleButton) {
      themeToggleButton.checked = isDarkMode;
    }
  }
  // Genre Management
  getCurrentGenre() {
    return this.state.currentGenre;
  }
  setCurrentGenre(genre) {
    this.state.currentGenre = genre;
  }
  // Track and Player Management
  getCurrentIsrc() {
    return this.state.currentIsrc;
  }
  setCurrentIsrc(isrc) {
    this.state.currentIsrc = isrc;
  }
  getCurrentPlayer() {
    return this.state.currentPlayer;
  }
  setCurrentPlayer(player) {
    this.state.currentPlayer = player;
  }
  setCurrentTrack(isrc, player) {
    this.state.currentIsrc = isrc;
    this.state.currentPlayer = player;
  }
  clearCurrentTrack() {
    this.state.currentIsrc = null;
    this.state.currentPlayer = null;
  }
  // DOM Element Caching
  getElement(id) {
    if (!this.domElements.has(id)) {
      const element = document.getElementById(id);
      if (element) {
        this.domElements.set(id, element);
      }
    }
    return this.domElements.get(id);
  }
  clearElementCache() {
    this.domElements.clear();
  }
  // Shimmer State Management
  setShimmerState(type, isActive, isInitialLoad = false) {
    if (type === "services") {
      this.state.shimmer.services = isActive;
    } else if (type === "playlist") {
      this.state.shimmer.playlist = isActive;
      this.state.shimmer.isInitialLoad = isInitialLoad;
    }
  }
  getShimmerState(type) {
    const shimmerValue = this.state.shimmer[type];
    return typeof shimmerValue === "boolean" ? shimmerValue : false;
  }
  isInitialLoad() {
    return this.state.shimmer.isInitialLoad;
  }
  showShimmer(type, isInitialLoad = false) {
    this.setShimmerState(type, true, isInitialLoad);
  }
  hideShimmer(type) {
    this.setShimmerState(type, false);
  }
  hideAllShimmers() {
    this.state.shimmer.services = false;
    this.state.shimmer.playlist = false;
    this.state.shimmer.isInitialLoad = false;
  }
  // Shimmer Type Management - explicit tracking of which shimmer layout to use
  setShimmerType(type) {
    this.state.shimmer.currentType = type;
  }
  getShimmerType() {
    return this.state.shimmer.currentType || SHIMMER_TYPES.TUNEMELD;
  }
  setShimmerTypeFromColumn(column) {
    // Convert column name to shimmer type
    if (column === TUNEMELD_RANK_FIELD || column === null) {
      this.setShimmerType(SHIMMER_TYPES.TUNEMELD);
    } else {
      this.setShimmerType(SHIMMER_TYPES.PLAYCOUNT);
    }
  }
  isShimmering(type) {
    if (type) {
      return this.getShimmerState(type);
    }
    return this.state.shimmer.services || this.state.shimmer.playlist;
  }
  getShimmerDebugInfo() {
    return {
      services: this.state.shimmer.services,
      playlist: this.state.shimmer.playlist,
      isInitialLoad: this.state.shimmer.isInitialLoad,
      anyActive: this.isShimmering(),
    };
  }
  registerModal(modalId, modalElement, overlayElement) {
    this.state.modals.activeDescriptionModals.add({
      id: modalId,
      modal: modalElement,
      overlay: overlayElement,
    });
  }
  clearAllModals() {
    this.state.modals.activeDescriptionModals.forEach(({ modal, overlay }) => {
      if (modal && modal.parentNode) {
        modal.remove();
      }
      if (overlay && overlay.parentNode) {
        overlay.remove();
      }
    });
    this.state.modals.activeDescriptionModals.clear();
  }
  getActiveModalCount() {
    return this.state.modals.activeDescriptionModals.size;
  }
}
export const stateManager = new StateManager();
