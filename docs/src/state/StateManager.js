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
class StateManager {
  constructor() {
    this.state = {
      sortColumn: null, // Will be set from backend default
      sortOrder: "asc",
      theme: null,
      currentGenre: null,
      defaultRankField: null, // Store the default from backend
    };
    this.domElements = new Map();
  }

  initializeFromDOM() {
    // Sort column will be set from backend default
    this.state.sortOrder = "asc";

    // Initialize theme from localStorage
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
}

export const stateManager = new StateManager();
