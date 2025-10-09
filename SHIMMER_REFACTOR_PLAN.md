# Shimmer Refactor Implementation Plan

## End Goal - Shimmer Behavior Specification

### INITIAL LOAD

**What shimmers:** EVERYTHING

- ✅ TuneMeld logo
- ✅ Service headers (Apple Music, SoundCloud, Spotify cards)
- ✅ Playlist title and description
- ✅ Genre buttons
- ✅ Ranking buttons
- ✅ Track list

### GENRE SWITCH

**What shimmers:** Service content + tracks (NOT buttons)

- ✅ Service headers (cards refresh with new genre data)
- ✅ TuneMeld playlist title/description
- ✅ Track list
- ❌ Genre buttons (stay visible)
- ❌ Ranking buttons (stay visible)

### RANK SWITCH

**What shimmers:** ONLY tracks

- ❌ Service headers (stay visible)
- ❌ Playlist title/description (stays visible)
- ❌ Genre buttons (stay visible)
- ❌ Ranking buttons (stay visible)
- ✅ Track list (re-sorts)

### Core Principle

**NO COMPLETE RE-RENDERS** - We hide/show specific elements, never destroy and recreate the entire playlist component.

## Refactored Shimmer Architecture

### New Function Structure - Two Separate Functions

```typescript
// SERVICE HEADERS SHIMMER (Apple Music, SoundCloud, Spotify cards)
function showServiceHeadersShimmer(): void {
  // Show shimmer for the 3 service cards at the top
  document.querySelectorAll(".service").forEach((service) => {
    let overlay = service.querySelector(".loading-overlay");
    if (!overlay) {
      overlay = createServiceShimmer();
      service.appendChild(overlay);
    }
    overlay.classList.add("active");
  });
}

// MAIN PLAYLIST SHIMMER (TuneMeld playlist section)
function showPlaylistShimmer(options: {
  showLogo?: boolean; // Initial load only
  showPlaylistInfo?: boolean; // Initial load + genre switch
  showGenreButtons?: boolean; // Initial load only
  showRankButtons?: boolean; // Initial load only
  showTracks?: boolean; // Always
}) {
  // Implementation will selectively show/hide elements in the main playlist area
}

// Usage examples:
// Initial load
showServiceHeadersShimmer();
showPlaylistShimmer({
  showLogo: true,
  showPlaylistInfo: true,
  showGenreButtons: true,
  showRankButtons: true,
  showTracks: true,
});

// Genre switch
showServiceHeadersShimmer();
showPlaylistShimmer({
  showLogo: false,
  showPlaylistInfo: true,
  showGenreButtons: false,
  showRankButtons: false,
  showTracks: true,
});

// Rank switch (no service header shimmer)
showPlaylistShimmer({
  showLogo: false,
  showPlaylistInfo: false,
  showGenreButtons: false,
  showRankButtons: false,
  showTracks: true,
});
```

## Implementation Phases (REVISED)

### What’s already shipped

- ✅ Service + playlist shimmer logic unified under `showShimmerLoaders` with explicit tracker logging.
- ✅ Tunemeld playlist render keeps the skeleton visible until **all** album artwork finishes loading; real rows fade in in a single step.
- ✅ Mutation observer + `TrackLoad` instrumentation catch any unexpected skeleton clears.
- ✅ CSS tightened so only the data tbody hides during the load; shimmer tbody remains visible at all times.

### Next milestones

1. **State-managed reveal orchestration** – move playlist/header reveal promises into `StateManager` so we can coordinate “skeleton vs. data” visibility from one hub (no scattered class toggles).
2. **Service header media gating** – reuse the playlist pattern for the top cards: the shimmer stays active until every service image/video resolves, then the entire header row fades in together.
3. **Componentised shimmers** – continue breaking the monolithic shimmer DOM into small creators that can be combined per scenario (initial load, genre switch, rank switch).
4. **Observability hooks** – emit standard debug events (`stateManager.logTransition(...)`) so console traces stay consistent without ad‑hoc logs.

### Phase 0: Refactor to Modular Shimmer Components

**Goal:** Break down the monolithic shimmer into reusable components that can be composed

**Key Insight:** The current `createPlaylistShimmer(includeControls, shimmerType)` creates everything as one big DOM element. We need to break this into separate functions that create individual shimmer components, which can then be conditionally assembled.

**Changes:**

1. Break down `createPlaylistShimmer()` into smaller component creators
2. Create new composition functions that assemble components based on options
3. Keep existing shimmer functions as wrappers initially

**Modular Component Structure:**

```typescript
// frontend/src/components/shimmer.ts

// STEP 1: Create individual shimmer component creators
// These return DOM elements that can be inserted anywhere

function createLogoShimmer(): HTMLDivElement {
  const logoShimmer = createElement("div", "shimmer shimmer-playlist-logo");
  return logoShimmer;
}

function createPlaylistInfoShimmer(): HTMLDivElement {
  const container = createElement("div", "playlist-header-shimmer");
  const titleRow = createElement("div", "playlist-title-shimmer");

  const logoShimmer = createElement("div", "shimmer shimmer-playlist-logo");
  const titleShimmer = createElement("div", "shimmer shimmer-playlist-title");
  const descShimmer = createElement("div", "shimmer shimmer-playlist-desc");

  titleRow.appendChild(logoShimmer);
  titleRow.appendChild(titleShimmer);
  titleRow.appendChild(descShimmer);
  container.appendChild(titleRow);

  return container;
}

function createGenreButtonsShimmer(): HTMLDivElement {
  const genreSection = createElement("div", "control-group-shimmer");
  const genreLabel = createElement("div", "shimmer shimmer-control-label");
  const genreButtons = createElement("div", "shimmer-buttons-row");

  for (let i = 0; i < 4; i++) {
    genreButtons.appendChild(createElement("div", "shimmer shimmer-button"));
  }

  genreSection.appendChild(genreLabel);
  genreSection.appendChild(genreButtons);
  return genreSection;
}

function createRankButtonsShimmer(): HTMLDivElement {
  const rankSection = createElement("div", "control-group-shimmer");
  const rankLabel = createElement("div", "shimmer shimmer-control-label");
  const rankButtons = createElement("div", "shimmer-buttons-row");

  for (let i = 0; i < 3; i++) {
    rankButtons.appendChild(createElement("div", "shimmer shimmer-button"));
  }

  rankSection.appendChild(rankLabel);
  rankSection.appendChild(rankButtons);
  return rankSection;
}

function createTracksShimmer(shimmerType: ShimmerType): HTMLDivElement {
  const tableContainer = createElement("div", "shimmer-table-container");
  tableContainer.appendChild(createShimmerTable(shimmerType));
  return tableContainer;
}

// STEP 2: Refactor the monolithic function to use components
function createPlaylistShimmer(
  includeControls: boolean = true,
  shimmerType: ShimmerType = SHIMMER_TYPES.TUNEMELD,
): HTMLDivElement {
  const overlay = createElement(
    "div",
    "loading-overlay loading-overlay-playlist",
  ) as HTMLDivElement;

  if (includeControls) {
    // Compose the full shimmer from individual components
    overlay.appendChild(createPlaylistInfoShimmer());
    overlay.appendChild(createGenreButtonsShimmer());
    overlay.appendChild(createRankButtonsShimmer());
  }

  // Always include tracks
  overlay.appendChild(createTracksShimmer(shimmerType));

  return overlay;
}

// STEP 3: New granular show functions that can insert components selectively
interface PlaylistShimmerOptions {
  showLogo?: boolean;
  showPlaylistInfo?: boolean;
  showGenreButtons?: boolean;
  showRankButtons?: boolean;
  showTracks?: boolean;
}

export function showPlaylistShimmer(options: PlaylistShimmerOptions): void {
  const mainPlaylist = document.querySelector(".main-playlist");
  if (!mainPlaylist) return;

  const playlistContent = mainPlaylist.querySelector(".playlist-content");
  if (!playlistContent) return;

  // Remove any existing shimmer first
  const existingShimmer = playlistContent.querySelector(
    ".loading-overlay-playlist",
  );
  if (existingShimmer) {
    existingShimmer.remove();
  }

  // Create a new shimmer container
  const shimmerContainer = createElement(
    "div",
    "loading-overlay loading-overlay-playlist",
  ) as HTMLDivElement;

  // Conditionally add components based on options
  if (options.showPlaylistInfo) {
    shimmerContainer.appendChild(createPlaylistInfoShimmer());
  }

  if (options.showGenreButtons) {
    shimmerContainer.appendChild(createGenreButtonsShimmer());
  }

  if (options.showRankButtons) {
    shimmerContainer.appendChild(createRankButtonsShimmer());
  }

  if (options.showTracks) {
    const shimmerType = stateManager.getShimmerType() as ShimmerType;
    shimmerContainer.appendChild(createTracksShimmer(shimmerType));
  }

  // Insert the composed shimmer
  playlistContent.appendChild(shimmerContainer);
  shimmerContainer.classList.add("active");
}

// SERVICE HEADERS remain separate
export function showServiceHeadersShimmer(): void {
  stateManager.showShimmer("services");

  document.querySelectorAll(".service").forEach((service) => {
    let overlay = service.querySelector(".loading-overlay");
    if (!overlay) {
      overlay = createServiceShimmer();
      service.appendChild(overlay);
    }
    overlay.classList.add("active");
  });
}

// STEP 4: Update wrapper functions to use new modular approach
export function showInitialShimmer(): void {
  // For initial load, we can still use the old monolithic approach
  // OR compose using the new functions
  showServiceHeadersShimmer();
  showPlaylistShimmer({
    showLogo: true,
    showPlaylistInfo: true,
    showGenreButtons: true,
    showRankButtons: true,
    showTracks: true,
  });
}

export function showGenreSwitchShimmer(): void {
  showServiceHeadersShimmer();
  showPlaylistShimmer({
    showPlaylistInfo: true,
    showTracks: true,
  });
}

export function showRankSwitchShimmer(): void {
  showPlaylistShimmer({
    showTracks: true,
  });
}
```

### Phase 1: Minimal Hide/Show (SAFE)

**Goal:** Prove hide/show concept without breaking anything

**Changes:**

1. Add `.hidden` utility class to `frontend/css/styles.css`
2. Implement `showPlaylistShimmer()` with hide/show logic
3. Test with overlay approach first
4. Verify initial load still works

**Test Points:**

- Initial page load shows all shimmers
- Genre switch shows only service + tracks
- Rank switch shows only tracks
- Content appears after shimmer

### Phase 2: DOM Structure Alignment

**Goal:** Align shimmer structure with real HTML

**Changes:**

1. Update shimmer HTML generation to match real structure
2. Use same classes as real elements with shimmer modifier
3. Keep as overlay for now

### Phase 3: Position Strategy Change

**Goal:** Switch from overlay to hide/show approach

**Changes:**

1. Change positioning from absolute overlay to static
2. Hide real elements when showing shimmer
3. Show real elements when hiding shimmer
4. Remove shimmer from DOM when done

### Phase 4: Spacing Standardization

**Goal:** Clean, consistent spacing

**Changes:**

1. Standardize all vertical spacing
2. Ensure no layout jumps during transitions

### Phase 5: Cleanup & Optimization

**Goal:** Final polish and verification

**Changes:**

1. Remove old code
2. Ensure no memory leaks
3. Performance optimization

## Original Commit Analysis (626d0b5)

**Commit Message:** "refactor: change shimmer from overlay to hide/show approach"
**Date:** Mon Oct 6 19:44:06 2025 -0400

### Files Changed

```
Makefile                            |   4 +-
frontend/css/playlist.css           |  21 ++++-
frontend/css/shimmer.css            |  43 ++++-------
frontend/css/styles.css             |   4 +
frontend/css/themes.css             |   8 +-
frontend/dev.js                     | 149 ++++++++++++++++++++++++++++++++++++
frontend/package.json               |   4 +-
frontend/src/components/playlist.ts |  15 ++++
frontend/src/components/shimmer.ts  | 133 ++++++++++++++++++++------------
```

## Key Changes Breakdown

### 1. Positioning Strategy Change

**BEFORE (ec60672):**

```typescript
// frontend/src/components/shimmer.ts:142-165
if (isInitialLoad) {
  const mainPlaylist = document.querySelector(".playlist.main-playlist");
  if (mainPlaylist) {
    let overlay = mainPlaylist.querySelector(".loading-overlay");
    if (!overlay) {
      overlay = createPlaylistShimmer(true, shimmerType);
      mainPlaylist.appendChild(overlay);
    }
    overlay.classList.add("active");
  }
}
```

**AFTER (626d0b5):**

```typescript
// frontend/src/components/shimmer.ts:167-183
if (isInitialLoad) {
  // Hide real elements
  playlistHeader?.classList.add("hidden");
  const controlGroups = playlistContent.querySelectorAll(".control-group");
  const playlistTable = playlistContent.querySelector(".playlist-table");
  controlGroups.forEach((group) => group.classList.add("hidden"));
  playlistTable?.classList.add("hidden");

  // Create and insert shimmer
  const shimmer = createPlaylistShimmer(true, shimmerType);
  playlistContent.appendChild(shimmer);
}
```

### 2. DOM Structure Changes

**BEFORE (ec60672):**

```typescript
// frontend/src/components/shimmer.ts:103-131
// Genre controls
const genreSection = createElement("div", "control-group-shimmer");
const genreLabel = createElement("div", "shimmer shimmer-control-label");
const genreButtons = createElement("div", "shimmer-buttons-row");
for (let i = 0; i < 4; i++) {
  genreButtons.appendChild(createElement("div", "shimmer shimmer-button"));
}
```

**AFTER (626d0b5):**

```typescript
// frontend/src/components/shimmer.ts:100-110
// Genre controls - using same structure as actual HTML
const genreSection = createElement("div", "control-group");
const genreLabel = createElement("label", "control-label shimmer");
const genreButtons = createElement("div", "genre-controls");
for (let i = 0; i < 4; i++) {
  genreButtons.appendChild(createElement("div", "sort-button shimmer"));
}
```

### 3. CSS Changes

**frontend/css/playlist.css:**

```css
/* Added position context */
.playlist-content {
  position: relative; /* Line 25 */
}

/* Standardized spacing */
.control-group {
  margin: 0; /* Line 365, changed from margin-bottom: var(--space-lg); margin-top: var(--space-lg); */
}

.control-label {
  margin-bottom: var(--space-md); /* Line 376, changed from var(--space-sm) */
}

.sort-controls {
  margin-bottom: var(--space-md); /* Line 384, changed from var(--space-xl) */
}

.genre-controls {
  margin-bottom: var(--space-md); /* Line 391, added */
}
```

**frontend/css/shimmer.css:**

```css
/* Changed positioning strategy */
.loading-overlay-playlist {
  position: static; /* Line 55, changed from absolute */
  display: block; /* Line 56 */
}
```

**frontend/css/styles.css:**

```css
/* Added hidden utility class */
.hidden {
  display: none !important; /* Line 4 */
}
```

### 4. Hide/Show Logic

**hideShimmerLoaders() changes:**

**BEFORE (ec60672):**

```typescript
// frontend/src/components/shimmer.ts:195-200
const overlays = document.querySelectorAll(".loading-overlay");
overlays.forEach((overlay) => {
  overlay.classList.remove("active");
});
```

**AFTER (626d0b5):**

```typescript
// frontend/src/components/shimmer.ts:208-240
// Show real playlist content and remove shimmer
const mainPlaylist = document.querySelector(".main-playlist");
if (mainPlaylist) {
  const playlistHeader = mainPlaylist.querySelector(".playlist-header");
  const playlistContent = mainPlaylist.querySelector(".playlist-content");

  // Show real header
  playlistHeader?.classList.remove("hidden");

  if (playlistContent) {
    // Show real controls and table
    const controlGroups = playlistContent.querySelectorAll(".control-group");
    const playlistTable = playlistContent.querySelector(".playlist-table");

    controlGroups.forEach((group) => group.classList.remove("hidden"));
    playlistTable?.classList.remove("hidden");

    // Remove shimmer overlay from DOM
    const shimmerOverlay = playlistContent.querySelector(
      ".loading-overlay-playlist",
    );
    if (shimmerOverlay) {
      shimmerOverlay.remove();
    }
  }
}
```

## Critical Bug to Avoid

The original implementation broke because it checked for `isInitialLoad` but this wasn't properly synchronized between the router and StateManager. The router had its own `isInitialLoad` flag but `stateManager.isInitialLoad()` returned `false` on actual initial load.

**Solution:** Ensure proper state initialization or use router's flag directly.

## Testing Checklist

- [ ] Initial page load shows full shimmer (logo, buttons, tracks)
- [ ] Genre switch shows appropriate shimmer (services + tracks, NO buttons)
- [ ] Rank switch shows only track shimmer
- [ ] No visual jumps or layout shifts
- [ ] Shimmer elements removed from DOM after hiding
- [ ] Fast switching doesn't create duplicate shimmers
- [ ] Mobile view works correctly
- [ ] Dark/light theme both work
- [ ] No complete re-renders of playlist component

## Rollback Plan

If any phase breaks functionality:

1. `git reset --hard ec60672` (current working version)
2. Review what went wrong
3. Adjust implementation plan
4. Try again with smaller changes
