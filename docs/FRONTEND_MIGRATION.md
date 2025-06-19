# TuneMeld Frontend Migration Plan

## Overview

Refactoring frontend architecture for better maintainability, clearer control flow, and removal of circular dependencies. Focus: **minimal changes, maximum impact**.

## Current Pain Points

- Circular dependencies: `selectors.js` ↔ `playlist.js`
- Scattered state management (DOM, localStorage, module-level)
- 373-line monolithic `playlist.js`
- Complex async initialization chains
- Inconsistent error handling

## Migration Strategy

### Phase 1: Foundation (CURRENT)

**Goal**: Remove circular dependencies, centralize state, extract API layer

#### 1.1 Create StateManager ✅

- [x] Create simple state management without DOM dependencies
- [x] Move current/sort state from DOM attributes to StateManager
- [x] Replace `getCurrentViewCountType()`, `getCurrentColumn()`, `getCurrentOrder()` functions
- [x] Update selectors.js to use StateManager instead of DOM
- [x] Add DOM initialization to keep state in sync

#### 1.2 Break Circular Dependencies ✅

- [x] Move shared state functions from `selectors.js` to `StateManager`
- [x] Update imports to remove `selectors.js` ↔ `playlist.js` cycle
- [x] Remove wrapper functions and inline StateManager calls directly
- [x] Test that functionality remains intact

#### 1.3 Extract API Service 🔄

- [ ] Create `ApiService.js` with all API calls
- [ ] Move API calls from `playlist.js`, `header.js`, `chart.js`
- [ ] Add consistent error handling

### Phase 2: Component Separation

**Goal**: Break down large modules, standardize patterns

#### 2.1 Split playlist.js

- [ ] Extract table rendering logic
- [ ] Extract sorting functionality
- [ ] Extract data transformation
- [ ] Keep event handling consolidated

#### 2.2 Standardize Event Handling

- [ ] Create event cleanup patterns
- [ ] Remove manual event listener management
- [ ] Centralize event registration

### Phase 3: State Migration

**Goal**: Move remaining DOM-based state to StateManager

#### 3.1 DOM State Elimination

- [ ] Move theme state from DOM/localStorage to StateManager
- [ ] Move selector values from DOM to StateManager
- [ ] Add reactive state updates

#### 3.2 Testing & Cleanup

- [ ] Ensure all functionality works
- [ ] Clean up unused functions
- [ ] Add error boundaries

## Current Progress

### ✅ Completed

- Migration plan document created
- Phase 1.1: StateManager implementation
- Phase 1.2: Circular dependencies broken

### 🔄 In Progress

- Phase 1.3: API service extraction

### ⏳ Pending

- Phase 2: Component separation
- Phase 3: State migration

## Files Changed This Session

- `/docs/FRONTEND_MIGRATION.md` - This migration document
- `/docs/StateManager.js` - New centralized state management (CREATED)
- `/docs/selectors.js` - Updated to use StateManager instead of DOM queries
- `/docs/main.js` - Added StateManager initialization from DOM
- (Additional files will be listed as migration progresses)

## Testing Checklist

- [ ] Genre selection works
- [ ] View count type selection works
- [ ] Table sorting works
- [ ] Header art loads
- [ ] Service players work
- [ ] Charts display correctly
- [ ] Theme toggle works
- [ ] All async operations complete properly

## Notes

- Keeping changes minimal to avoid breaking functionality
- Testing after each phase before proceeding
- Maintaining backward compatibility during transition
