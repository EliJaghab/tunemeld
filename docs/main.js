document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
  const genreSelector = document.getElementById('genre-selector');
  const rankSelector = document.getElementById('rank-selector');
  
  let currentGenre = genreSelector.value || 'pop';
  let currentRank = rankSelector.value || 'default';
  
  updateGenreData(currentGenre, currentRank, true);

  genreSelector.addEventListener('change', function () {
    currentGenre = genreSelector.value;
    currentRank = rankSelector.value;
    updateGenreData(currentGenre, currentRank, true);
  });

  rankSelector.addEventListener('change', function () {
    const newRank = rankSelector.value;
    currentRank = newRank;
    updateMainPlaylist(currentGenre, currentRank);
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

async function updateGenreData(genre, rank, updateAll = false) {
  try {
    showSkeletonLoaders();
    if (updateAll) {
      await fetchAndDisplayLastUpdated(genre);
      await fetchAndDisplayHeaderArt(genre);
      await fetchAndDisplayPlaylists(genre);
    }
    await updateMainPlaylist(genre, rank);
    hideSkeletonLoaders();
    resetCollapseStates();
    addToggleEventListeners();
  } catch (error) {
    console.error('Error updating genre data:', error);
  }
}

async function updateMainPlaylist(genre, rank) {
  try {
    const url = `${API_BASE_URL}/api/main-playlist?genre=${genre}`;
    await fetchAndDisplayData(url, 'main-playlist-data-placeholder', true, rank);
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
