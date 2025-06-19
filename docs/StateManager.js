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
      viewCountType: "total-view-count",
      sortColumn: "rank",
      sortOrder: "asc",
    };
  }

  initializeFromDOM() {
    const viewCountSelector = document.getElementById("view-count-type-selector");
    if (viewCountSelector) {
      this.state.viewCountType = viewCountSelector.value || "total-view-count";
    }

    const sortButton = document.querySelector(".sort-button[data-order]");
    if (sortButton) {
      this.state.sortColumn = sortButton.getAttribute("data-column") || "rank";
      this.state.sortOrder = sortButton.getAttribute("data-order") || "asc";
    }
  }

  getViewCountType() {
    return this.state.viewCountType;
  }

  setViewCountType(type) {
    this.state.viewCountType = type;
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

  setCurrentOrder(order) {
    this.state.sortOrder = order;
  }
}

export const stateManager = new StateManager();
