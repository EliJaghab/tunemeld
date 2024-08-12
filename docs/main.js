import { fetchAndDisplayHeaderArt, hideSkeletonLoaders, showSkeletonLoaders  } from './header.js';
import { addToggleEventListeners, fetchAndDisplayLastUpdated, fetchAndDisplayPlaylists, resetCollapseStates, setupSortButtons, sortTable, updateMainPlaylist } from './playlist.js';
import { setupGenreSelector, setupViewCountTypeSelector } from './selectors.js';
import { setupBodyClickListener, setupClosePlayerButton} from './servicePlayer.js';

document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
  const genreSelector = document.getElementById('genre-selector');
  const viewCountTypeSelector = document.getElementById('view-count-type-selector');

  let currentGenre = genreSelector.value || 'pop';
  let viewCountType = viewCountTypeSelector.value || 'total-view-count';

  updateGenreData(currentGenre, viewCountType, true);

  setupGenreSelector(genreSelector);
  setupViewCountTypeSelector(viewCountTypeSelector);
  setupBodyClickListener();
  setupSortButtons();
  setupClosePlayerButton();
  
}

async function updateGenreData(genre, viewCountType, updateAll = false) {
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
  } catch (error) {
    console.error('Error updating genre data:', error);
  }
}