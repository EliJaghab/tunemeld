import { setupSortButtons } from './playlist.js';
import { setupGenreSelector, setupViewCountTypeSelector, updateGenreData } from './selectors.js';
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