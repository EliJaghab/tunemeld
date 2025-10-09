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

import {
  SHIMMER_TYPES,
  TUNEMELD_RANK_FIELD,
  type ShimmerType,
} from "../config/constants.js";
import { debugLog } from "@/config/config";
import type { Rank, Genre, ButtonLabel, ButtonLabels } from "@/types";

interface ShimmerState {
  services: boolean;
  playlist: boolean;
  isInitialLoad: boolean;
  currentType: ShimmerType;
  [key: string]: boolean | string; // Index signature for dynamic access
}

interface ModalInfo {
  id: string;
  modal: HTMLElement;
  overlay: HTMLElement;
}

interface LoadingState {
  tracksLoaded: boolean;
  genreButtonsLoaded: boolean;
  rankButtonsLoaded: boolean;
  genreImagesLoaded: boolean;
  serviceDataLoaded: boolean;
  playlistDataLoaded: boolean;
}

interface AppState {
  sortColumn: string | null;
  sortOrder: string;
  theme: string | null;
  currentGenre: string | null;
  currentIsrc: string | null;
  currentPlayer: string | null;
  defaultRankField: string | null;
  ranks: Rank[];
  genres: Genre[];
  buttonLabels: ButtonLabels | null;
  shimmer: ShimmerState;
  loading: LoadingState;
  modals: {
    activeDescriptionModals: Set<ModalInfo>;
  };
}

const stateDebug = (message: string, meta?: unknown) => {
  debugLog("StateManager", message, meta);
};

class StateManager {
  private state: AppState;
  private domElements: Map<string, HTMLElement>;
  private serviceHeaderRevealToken: symbol | null;
  constructor() {
    this.state = {
      sortColumn: null, // Will be set from backend default
      sortOrder: "asc",
      theme: null,
      currentGenre: null,
      currentIsrc: null,
      currentPlayer: null,
      defaultRankField: null, // Store the default from backend
      ranks: [],
      genres: [],
      buttonLabels: null,
      shimmer: {
        services: false,
        playlist: false,
        isInitialLoad: false,
        currentType: SHIMMER_TYPES.TUNEMELD,
      },
      loading: {
        tracksLoaded: false,
        genreButtonsLoaded: false,
        rankButtonsLoaded: false,
        genreImagesLoaded: false,
        serviceDataLoaded: false,
        playlistDataLoaded: false,
      },
      modals: {
        activeDescriptionModals: new Set(),
      },
    };
    this.domElements = new Map();
    this.serviceHeaderRevealToken = null;
  }

  initializeFromDOM(): void {
    // Sort column will be set from backend default
    this.state.sortOrder = "asc";

    // Initialize theme - it may already be applied by inline script
    const storedTheme = localStorage.getItem("theme");
    this.state.theme = storedTheme || this.getTimeBasedTheme();
  }

  getTimeBasedTheme(): string {
    const hour = new Date().getHours();
    return hour >= 19 || hour < 7 ? "dark" : "light";
  }

  getCurrentColumn(): string | null {
    return this.state.sortColumn;
  }

  setCurrentColumn(column: string): void {
    this.state.sortColumn = column;
  }

  getCurrentOrder(): string {
    return this.state.sortOrder;
  }

  isRankActive(rankSortField: string): boolean {
    return rankSortField === this.getCurrentColumn();
  }

  setCurrentOrder(order: string): void {
    this.state.sortOrder = order;
  }

  setDefaultRankField(field: string): void {
    this.state.defaultRankField = field;
    // If no sort column set yet, use the default
    if (!this.state.sortColumn) {
      this.state.sortColumn = field;
    }
  }

  getDefaultRankField(): string | null {
    return this.state.defaultRankField;
  }

  isSortingByDefaultRank(): boolean {
    return this.state.sortColumn === this.state.defaultRankField;
  }

  // Theme Management
  getTheme(): string | null {
    return this.state.theme;
  }

  setTheme(theme: string): void {
    this.state.theme = theme;
    localStorage.setItem("theme", theme);
    this.applyTheme(theme);
  }

  toggleTheme(): string {
    const newTheme = this.state.theme === "dark" ? "light" : "dark";
    this.setTheme(newTheme);
    return newTheme;
  }

  applyTheme(theme: string): void {
    const isDarkMode = theme === "dark";

    // Remove loading state and apply proper theme
    document.documentElement.classList.remove("dark-mode-loading");
    document.body.classList.toggle("dark-mode", isDarkMode);

    const themeToggleButton = this.getElement("theme-toggle-button") as
      | HTMLInputElement
      | undefined;
    if (themeToggleButton) {
      themeToggleButton.checked = isDarkMode;
    }
  }

  // Genre Management
  getCurrentGenre(): string | null {
    return this.state.currentGenre;
  }

  setCurrentGenre(genre: string): void {
    this.state.currentGenre = genre;
  }

  // Track and Player Management
  getCurrentIsrc(): string | null {
    return this.state.currentIsrc;
  }

  setCurrentIsrc(isrc: string): void {
    this.state.currentIsrc = isrc;
  }

  getCurrentPlayer(): string | null {
    return this.state.currentPlayer;
  }

  setCurrentPlayer(player: string): void {
    this.state.currentPlayer = player;
  }

  setCurrentTrack(isrc: string, player: string): void {
    this.state.currentIsrc = isrc;
    this.state.currentPlayer = player;
  }

  clearCurrentTrack(): void {
    this.state.currentIsrc = null;
    this.state.currentPlayer = null;
  }

  // DOM Element Caching
  getElement(id: string): HTMLElement | undefined {
    if (!this.domElements.has(id)) {
      const element = document.getElementById(id);
      if (element) {
        this.domElements.set(id, element);
      }
    }
    return this.domElements.get(id);
  }

  clearElementCache(): void {
    this.domElements.clear();
  }

  // Shimmer State Management
  setShimmerState(
    type: string,
    isActive: boolean,
    isInitialLoad = false,
  ): void {
    if (type === "services") {
      this.state.shimmer.services = isActive;
    } else if (type === "playlist") {
      this.state.shimmer.playlist = isActive;
    }

    // Set isInitialLoad flag globally, not tied to shimmer type
    // Only set to true if explicitly passed, don't override back to false
    if (isInitialLoad) {
      this.state.shimmer.isInitialLoad = isInitialLoad;
    }
  }

  getShimmerState(type: string): boolean {
    const shimmerValue = this.state.shimmer[type as keyof ShimmerState];
    return typeof shimmerValue === "boolean" ? shimmerValue : false;
  }

  isInitialLoad(): boolean {
    return this.state.shimmer.isInitialLoad;
  }

  showShimmer(type: string, isInitialLoad: boolean = false): void {
    this.setShimmerState(type, true, isInitialLoad);
  }

  hideShimmer(type: string): void {
    this.setShimmerState(type, false);
  }

  hideAllShimmers(): void {
    this.state.shimmer.services = false;
    this.state.shimmer.playlist = false;
    this.state.shimmer.isInitialLoad = false;
  }

  registerServiceHeaderReveal(promise: Promise<void>): void {
    stateDebug("registerServiceHeaderReveal: registered");
    const token = Symbol("serviceHeaderReveal");
    this.serviceHeaderRevealToken = token;

    const trackedPromise = promise
      .catch((error: unknown) => {
        stateDebug("registerServiceHeaderReveal: promise rejected", {
          error,
        });
      })
      .then(() => {
        if (this.serviceHeaderRevealToken === token) {
          stateDebug("registerServiceHeaderReveal: resolved");
          this.markLoaded("serviceDataLoaded");
        } else {
          stateDebug(
            "registerServiceHeaderReveal: resolved but token mismatch",
          );
        }
      });

    trackedPromise.finally(() => {
      if (this.serviceHeaderRevealToken === token) {
        this.serviceHeaderRevealToken = null;
      }
    });
  }

  markInitialLoadComplete(): void {
    this.state.shimmer.isInitialLoad = false;
  }

  // Shimmer Type Management - explicit tracking of which shimmer layout to use
  setShimmerType(type: ShimmerType): void {
    this.state.shimmer.currentType = type;
  }

  getShimmerType(): ShimmerType {
    return this.state.shimmer.currentType || SHIMMER_TYPES.TUNEMELD;
  }

  setShimmerTypeFromColumn(column: string | null): void {
    // Convert column name to shimmer type
    // Each rank has its own specific shimmer layout
    if (column === TUNEMELD_RANK_FIELD || column === null) {
      this.setShimmerType(SHIMMER_TYPES.TUNEMELD);
    } else if (column === "total-plays") {
      this.setShimmerType(SHIMMER_TYPES.TOTAL_PLAYS);
    } else if (column === "trending") {
      this.setShimmerType(SHIMMER_TYPES.TRENDING);
    } else {
      // Default fallback
      this.setShimmerType(SHIMMER_TYPES.TUNEMELD);
    }
  }

  setShimmerTypeFromSortField(sortField: string): void {
    // Centralized logic for determining shimmer type from sort field
    if (sortField === TUNEMELD_RANK_FIELD) {
      this.setShimmerType(SHIMMER_TYPES.TUNEMELD);
    } else if (sortField === "total-plays") {
      this.setShimmerType(SHIMMER_TYPES.TOTAL_PLAYS);
    } else if (sortField === "trending") {
      this.setShimmerType(SHIMMER_TYPES.TRENDING);
    } else {
      // Default fallback
      this.setShimmerType(SHIMMER_TYPES.TUNEMELD);
    }
  }

  isShimmering(type?: string | null): boolean {
    if (type) {
      return this.getShimmerState(type);
    }
    return this.state.shimmer.services || this.state.shimmer.playlist;
  }

  getShimmerDebugInfo(): {
    services: boolean;
    playlist: boolean;
    isInitialLoad: boolean;
    anyActive: boolean;
  } {
    return {
      services: this.state.shimmer.services,
      playlist: this.state.shimmer.playlist,
      isInitialLoad: this.state.shimmer.isInitialLoad,
      anyActive: this.isShimmering(),
    };
  }

  registerModal(
    modalId: string,
    modalElement: HTMLElement,
    overlayElement: HTMLElement,
  ): void {
    this.state.modals.activeDescriptionModals.add({
      id: modalId,
      modal: modalElement,
      overlay: overlayElement,
    });
  }

  clearAllModals(): void {
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

  getActiveModalCount(): number {
    return this.state.modals.activeDescriptionModals.size;
  }

  // Loading State Management
  markLoaded(component: keyof LoadingState): void {
    stateDebug(`markLoaded:${component}`);
    this.state.loading[component] = true;
    this.checkIfFullyLoaded();
  }

  resetLoadingState(): void {
    this.state.loading = {
      tracksLoaded: false,
      genreButtonsLoaded: false,
      rankButtonsLoaded: false,
      genreImagesLoaded: false,
      serviceDataLoaded: false,
      playlistDataLoaded: false,
    };
  }

  isFullyLoaded(): boolean {
    return Object.values(this.state.loading).every((loaded) => loaded);
  }

  checkIfFullyLoaded(): void {
    stateDebug("checkIfFullyLoaded: checking if all components are loaded");
    // Only hide shimmer when ALL components are loaded
    if (this.state.shimmer.isInitialLoad) {
      const allLoaded =
        this.state.loading.tracksLoaded &&
        this.state.loading.genreButtonsLoaded &&
        this.state.loading.rankButtonsLoaded &&
        this.state.loading.genreImagesLoaded &&
        this.state.loading.serviceDataLoaded &&
        this.state.loading.playlistDataLoaded;

      stateDebug(`checkIfFullyLoaded: allLoaded = ${allLoaded}`);
      if (allLoaded) {
        stateDebug("checkIfFullyLoaded: all components loaded, hiding shimmer");
        // Import dynamically to avoid circular dependency
        import("@/components/shimmer").then(({ hideShimmerLoaders }) => {
          hideShimmerLoaders();
        });
      }
    }
  }

  async preloadImages(urls: string[]): Promise<void> {
    const promises = urls.map((url) => {
      return new Promise<void>((resolve) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => resolve(); // Resolve even on error to not block
        img.src = url;
      });
    });
    await Promise.all(promises);
  }

  // Static Configuration Management
  setRanks(ranks: Rank[]): void {
    this.state.ranks = ranks;
  }

  getRanks(): Rank[] {
    return this.state.ranks;
  }

  setGenres(genres: Genre[]): void {
    this.state.genres = genres;
  }

  getGenres(): Genre[] {
    return this.state.genres;
  }

  setButtonLabels(labels: ButtonLabels): void {
    this.state.buttonLabels = labels;
  }

  getButtonLabels(): ButtonLabels | null {
    return this.state.buttonLabels;
  }

  getButtonLabel(type: keyof ButtonLabels): ButtonLabel[] {
    return this.state.buttonLabels?.[type] || [];
  }
}

export const stateManager = new StateManager();
