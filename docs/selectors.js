import { fetchAndDisplayHeaderArt, hideSkeletonLoaders, showSkeletonLoaders  } from './header.js';
import { addToggleEventListeners, fetchAndDisplayLastUpdated, fetchAndDisplayPlaylists, resetCollapseStates, setupSortButtons, sortTable, updateMainPlaylist } from './playlist.js';
import { setupBodyClickListener } from './servicePlayer.js';

export async function updateGenreData(genre, viewCountType, updateAll = false) {
    try {
      showSkeletonLoaders();
      if (updateAll) {
        await fetchAndDisplayLastUpdated(genre);
        await fetchAndDisplayHeaderArt(genre);
        await fetchAndDisplayPlaylists(genre);
      }
      await updateMainPlaylist(genre, viewCountType);
      sortTable('rank', 'asc', 'total-view-count');
      hideSkeletonLoaders();
      resetCollapseStates();
      addToggleEventListeners();
      setupBodyClickListener(genre);
    } catch (error) {
      console.error('Error updating genre data:', error);
    }
  }

export function setupGenreSelector(genreSelector) {
    genreSelector.addEventListener('change', function () {
      const currentGenre = genreSelector.value;
      updateGenreData(currentGenre, getCurrentViewCountType(), true);
    });
  }
  
  export function setupViewCountTypeSelector(viewCountTypeSelector) {
    viewCountTypeSelector.addEventListener('change', function () {
      const viewCountType = viewCountTypeSelector.value;
      sortTable(getCurrentColumn(), getCurrentOrder(), viewCountType);
    });
  }
  
  export function getCurrentViewCountType() {
    return document.getElementById('view-count-type-selector').value || 'total-view-count';
  }
  
  export function getCurrentColumn() {
    return document.querySelector('.sort-button[data-order]').getAttribute('data-column') || 'rank';
  }
  
  export function getCurrentOrder() {
    return document.querySelector('.sort-button[data-order]').getAttribute('data-order') || 'asc';
  }
  
  export function setCurrentColumn(column) {
    document.querySelector('.sort-button[data-column]').setAttribute('data-column', column);
  }
  
  export function setCurrentOrder(order) {
    document.querySelector('.sort-button[data-order]').setAttribute('data-order', order);
  }
  