document.addEventListener('DOMContentLoaded', initializeApp);

document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
  const genreSelector = document.getElementById('genre-selector');
  
  let currentGenre = genreSelector.value || 'pop';
  
  updateGenreData(currentGenre, true);

  genreSelector.addEventListener('change', function () {
    currentGenre = genreSelector.value;
    updateGenreData(currentGenre, true);
  });

  document.querySelectorAll('.sort-button').forEach(button => {
    button.addEventListener('click', function () {
      const column = button.getAttribute('data-column');
      const order = button.getAttribute('data-order');
      const newOrder = order === 'desc' ? 'asc' : 'desc';
      button.setAttribute('data-order', newOrder);
      sortTable(column, newOrder);
    });
  });
}

const useProdBackend = true;

function getApiBaseUrl() {
  if (useProdBackend) {
    return 'https://tunemeld.com';
  }
  
  return window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8787'
    : 'https://tunemeld.com';
}

const API_BASE_URL = getApiBaseUrl();

async function updateGenreData(genre, updateAll = false) {
  try {
    showSkeletonLoaders();
    if (updateAll) {
      await fetchAndDisplayLastUpdated(genre);
      await fetchAndDisplayHeaderArt(genre);
      await fetchAndDisplayPlaylists(genre);
    }
    await updateMainPlaylist(genre);
    sortTable('rank', 'asc');
    hideSkeletonLoaders();
    resetCollapseStates();
    addToggleEventListeners();
  } catch (error) {
    console.error('Error updating genre data:', error);
  }
}

async function updateMainPlaylist(genre) {
  try {
    const url = `${API_BASE_URL}/api/main-playlist?genre=${genre}`;
    await fetchAndDisplayData(url, 'main-playlist-data-placeholder', true);
  } catch (error) {
    console.error('Error updating main playlist:', error);
  }
}

async function fetchAndDisplayLastUpdated(genre) {
  const url = `${API_BASE_URL}/api/last-updated?genre=${genre}`;
  await fetchAndDisplayData(url, 'last-updated');
}

async function fetchAndDisplayHeaderArt(genre) {
  const url = `${API_BASE_URL}/api/header-art?genre=${genre}`;
  await fetchAndDisplayData(url, 'header-art');
}

async function fetchAndDisplayPlaylists(genre) {
  const services = ['AppleMusic', 'SoundCloud', 'Spotify'];
  for (const service of services) {
    await fetchAndDisplayData(`${API_BASE_URL}/api/service-playlist?genre=${genre}&service=${service}`, `${service.toLowerCase()}-data-placeholder`);
  }
}
